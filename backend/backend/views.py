# backend/views.py (Adjust import if needed)
from rest_framework import generics
from rest_framework.response import Response # <<< Make sure Response is imported
# Adjust model/serializer imports based on your app structure
from .models import Point
from .serializers import PointSerializer, PointReplaySerializer
import traceback # Import traceback for detailed errors

class PointListView(generics.ListAPIView):
    """
    Lists all recorded points available for replay.
    Ordered by most recent first. Includes pagination.
    """
    queryset = Point.objects.filter(recorded_end_time__isnull=False).order_by('-recorded_start_time')
    serializer_class = PointSerializer
    # Optional: Add pagination if the list gets long
    # from rest_framework.pagination import PageNumberPagination
    # pagination_class = PageNumberPagination # You'd need to configure page size in settings

class PointReplayView(generics.RetrieveAPIView):
    """
    Retrieves a specific point along with all its coordinates for replay.
    Includes debugging for coordinate retrieval.
    Coordinates are ordered by relative_time_ms (defined in Coordinate model Meta).
    """
    # OPTIMIZATION: Prefetch related coordinates to potentially improve performance
    # Ensure 'coordinates' matches the related_name in Coordinate model
    queryset = Point.objects.prefetch_related('coordinates').all()
    serializer_class = PointReplaySerializer
    lookup_field = 'pk' # Use primary key for lookup

    # Override retrieve for debugging
    def retrieve(self, request, *args, **kwargs):
        print(f"\n--- [Replay View] Processing request for Point PK: {kwargs.get('pk')} ---")
        try:
            instance = self.get_object() # Get the specific Point object based on pk
            print(f"--- [Replay View] Fetched Point object ID: {instance.id} ---")

            # --- DEBUG: Explicitly check related coordinates BEFORE serialization ---
            coordinate_count = 0 # Default count
            related_coords_manager = None
            try:
                # Access the related manager using the correct related_name ('coordinates')
                related_coords_manager = instance.coordinates
                coordinate_count = related_coords_manager.count()
                print(f"--- [Replay View] DB Coordinate Count via 'instance.coordinates.count()': {coordinate_count} ---")

                # More detailed check if count is zero unexpectedly
                if coordinate_count == 0:
                     all_coords_for_point = Coordinate.objects.filter(point=instance).count()
                     print(f"--- [Replay View] DB Coordinate Count via direct filter (Coordinate.objects.filter(point=instance)): {all_coords_for_point} ---")
                     if all_coords_for_point > 0:
                         print(f"--- [Replay View] MISMATCH! Related manager count is 0, but direct filter found coordinates. Check related_name/prefetching? ---")

                # Optionally print a few coordinate IDs fetched this way for sanity check
                if coordinate_count > 0:
                   print(f"--- [Replay View] First few coord IDs from DB via related manager: {[c.id for c in related_coords_manager.all()[:5]]} ---")

            except AttributeError:
                 # This error means the related_name is WRONG or object setup failed
                 print(f"--- [Replay View] FATAL ERROR: AttributeError accessing 'instance.coordinates'. Check 'related_name' on Coordinate.point ForeignKey in models.py! It must be 'coordinates'. ---")
                 # Print available attributes to help debug
                 print(f"--- [Replay View] Attributes available on instance: {dir(instance)} ---")
            except Exception as e:
                print(f"--- [Replay View] Error accessing coordinates via related manager: {e} ---")
                print(traceback.format_exc()) # Print full traceback for unexpected errors


            # --- DEBUG: Proceed with standard serialization ---
            print(f"--- [Replay View] Getting serializer for Point {instance.id}... ---")
            serializer = self.get_serializer(instance)
            print(f"--- [Replay View] Serializer instance created. Serializing data... ---")
            try:
                serialized_data = serializer.data
                print(f"--- [Replay View] Serialization complete. ---")
            except Exception as ser_err:
                 print(f"--- [Replay View] FATAL ERROR during serialization: {ser_err} ---")
                 print(traceback.format_exc())
                 # Return an error response if serialization fails
                 return Response({"error": "Serialization failed", "details": str(ser_err)}, status=500)


            # --- DEBUG: Check the data AFTER serialization ---
            coords_in_response = serialized_data.get('coordinates', None) # Use .get() for safety
            print(f"--- [Replay View] Type of 'coordinates' key in final serialized data: {type(coords_in_response)} ---")

            if isinstance(coords_in_response, list):
                print(f"--- [Replay View] Length of 'coordinates' list in final serialized data: {len(coords_in_response)} ---")
                # Optionally print first few serialized coords
                if len(coords_in_response) > 0:
                    print(f"--- [Replay View] First 3 serialized coords (or fewer): {coords_in_response[:3]} ---")
                elif coordinate_count > 0:
                     print(f"--- [Replay View] WARNING: DB count was {coordinate_count}, but serialized list is empty! Check PointReplaySerializer fields and CoordinateSerializer. ---")
            elif coords_in_response is None:
                 print(f"--- [Replay View] WARNING: 'coordinates' key is missing from serialized data! Check PointReplaySerializer fields. ---")
            else:
                 print(f"--- [Replay View] WARNING: 'coordinates' key in serialized data is not a list! Check PointReplaySerializer. Type is {type(coords_in_response)}. ---")

            print(f"--- [Replay View] Returning response for Point PK: {kwargs.get('pk')} ---\n")
            return Response(serialized_data) # Return the serialized data

        except Point.DoesNotExist:
             print(f"--- [Replay View] Point with PK {kwargs.get('pk')} does not exist. ---")
             # Let standard DRF handle the 404 response
             raise
        except Exception as e:
            print(f"--- [Replay View] UNEXPECTED ERROR in retrieve method: {e} ---")
            print(traceback.format_exc())
            # Return a generic server error response
            return Response({"error": "An unexpected server error occurred", "details": str(e)}, status=500)# tracker/views.py
from rest_framework import generics
from rest_framework.response import Response
from .models import Point
from .serializers import PointSerializer, PointReplaySerializer

class PointListView(generics.ListAPIView):
    """
    Lists all recorded points available for replay.
    Ordered by most recent first.
    """
    queryset = Point.objects.filter(recorded_end_time__isnull=False).order_by('-recorded_start_time') # Only completed points
    serializer_class = PointSerializer

class PointReplayView(generics.RetrieveAPIView):
    """
    Retrieves a specific point along with all its coordinates for replay.
    Coordinates are ordered by relative_time_ms.
    """
    queryset = Point.objects.all()
    serializer_class = PointReplaySerializer
    lookup_field = 'pk' # 'pk' is the default, can be 'id'
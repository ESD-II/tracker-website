# minimal_gpu_test.py
import bpy
import sys
import time

print(f"--- Minimal GPU Test Start (Blender {bpy.app.version_string}) ---")

try:
    print("Enabling Cycles addon...")
    # Use try-except for addon enable, as it might already be enabled or fail silently sometimes
    try:
        bpy.ops.preferences.addon_enable(module='cycles')
        print("bpy.ops.preferences.addon_enable(module='cycles') executed.")
    except Exception as e:
        print(f"Warning: Exception during addon_enable: {e}")

    # Add a small delay to allow potential background processes to settle
    time.sleep(1.0)

    print("Accessing preferences...")
    cycles_prefs = bpy.context.preferences.addons.get('cycles', None)
    if not cycles_prefs:
        print("FATAL ERROR: bpy.context.preferences.addons.get('cycles', None) returned None.")
        sys.exit(1)

    cycles_prefs = cycles_prefs.preferences
    if not cycles_prefs:
        print("FATAL ERROR: cycles_prefs.preferences is None.")
        sys.exit(1)
    print("Preferences accessed.")

    # --- Device Query ---
    all_devices = None
    try:
        print("Attempting cycles_prefs.get_devices()...")
        all_devices = cycles_prefs.get_devices() # Primary method for older Blender versions
        if all_devices is None:
            print("Result: cycles_prefs.get_devices() returned None.")
        elif not all_devices:
            print("Result: cycles_prefs.get_devices() returned an empty list [].")
        else:
            print(f"Result: cycles_prefs.get_devices() returned: {[(d.name, d.type) for d in all_devices]}")

    except AttributeError:
        print("AttributeError: cycles_prefs.get_devices() does not exist. This is unexpected for 4.3.")
        # If get_devices doesn't exist, maybe try get_devices_for_type as a last resort?
        print("Trying get_devices_for_type('CUDA') as fallback...")
        try:
             cuda_devices_fallback = cycles_prefs.get_devices_for_type('CUDA')
             if cuda_devices_fallback is None:
                  print("Fallback get_devices_for_type('CUDA') returned None.")
             elif not cuda_devices_fallback:
                  print("Fallback get_devices_for_type('CUDA') returned empty list [].")
             else:
                  print(f"Fallback get_devices_for_type('CUDA') returned: {[(d.name, d.type) for d in cuda_devices_fallback]}")
        except Exception as e_fallback:
             print(f"Error during fallback get_devices_for_type: {e_fallback}")

    except Exception as e:
        print(f"UNEXPECTED ERROR during get_devices(): {e}")


    # --- Test specific type query (even if get_devices failed) ---
    print("\nAttempting cycles_prefs.get_devices_for_type('CUDA')...")
    try:
        cuda_devices = cycles_prefs.get_devices_for_type('CUDA')
        if cuda_devices is None:
            print("Result: get_devices_for_type('CUDA') returned None.")
        elif not cuda_devices:
            print("Result: get_devices_for_type('CUDA') returned empty list [].")
        else:
            print(f"Result: get_devices_for_type('CUDA') returned: {[(d.name, d.type) for d in cuda_devices]}")
    except AttributeError:
         print("AttributeError: get_devices_for_type does not exist.")
    except Exception as e:
         print(f"Error during get_devices_for_type('CUDA'): {e}")


    print("\nAttempting cycles_prefs.get_devices_for_type('OPTIX')...")
    try:
        optix_devices = cycles_prefs.get_devices_for_type('OPTIX')
        if optix_devices is None:
            print("Result: get_devices_for_type('OPTIX') returned None.")
        elif not optix_devices:
            print("Result: get_devices_for_type('OPTIX') returned empty list [].")
        else:
            print(f"Result: get_devices_for_type('OPTIX') returned: {[(d.name, d.type) for d in optix_devices]}")
    except AttributeError:
         print("AttributeError: get_devices_for_type does not exist.")
    except Exception as e:
         print(f"Error during get_devices_for_type('OPTIX'): {e}")


except Exception as e:
    print(f"FATAL ERROR in script: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n--- Minimal GPU Test End ---")
# Script finishes, Blender will exit
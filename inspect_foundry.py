from foundry_local import FoundryLocalManager
import inspect

print("FoundryLocalManager signature:")
print(inspect.signature(FoundryLocalManager))

print("\nClass methodları:")
for name in dir(FoundryLocalManager):
    if not name.startswith("_"):
        print(name)

print("\nInstance methodları:")
try:
    manager = FoundryLocalManager()
    for name in dir(manager):
        if not name.startswith("_"):
            print(name)
except Exception as e:
    print("Manager boş başlatılamadı:", e)
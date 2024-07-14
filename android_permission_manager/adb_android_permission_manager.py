import subprocess
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def run_adb_command(command):
    print(f"Ausführung des ADB-Befehls: adb {' '.join(command)}")
    result = subprocess.run(["adb"] + command, capture_output=True, text=True)
    return result.stdout.strip()

def get_app_name(package):
    output = run_adb_command(["shell", "dumpsys", "package", package, "|", "grep", "versionName"])
    match = re.search(r'versionName=(.+)', output)
    if match:
        return match.group(1)
    return package

def get_app_permissions(package):
    permissions = {
        "RUN_IN_BACKGROUND": False,
        "SCHEDULE_EXACT_ALARM": False,
        "ACCESS_BACKGROUND_LOCATION": False
    }
    
    output = run_adb_command(["shell", "dumpsys", "package", package])
    
    for perm in permissions:
        if f"android.permission.{perm}" in output:
            permissions[perm] = True
    
    return permissions

def get_app_info(package):
    app_name = get_app_name(package)
    permissions = get_app_permissions(package)
    has_background_perm = any(permissions.values())
    
    return {
        "name": app_name,
        "package": package,
        "permissions": permissions,
        "has_background_perm": has_background_perm
    }

def get_installed_apps():
    user_apps = []
    system_apps = []
    
    print("Abrufen der installierten Apps...")
    for app_type in ["-3", "-s"]:
        output = run_adb_command(["shell", "pm", "list", "packages", "-f", app_type])
        packages = re.findall(r'package:(.+)=(.+)', output)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_app_info, package) for _, package in packages]
            
            for future in tqdm(as_completed(futures), total=len(packages), desc=f"Verarbeite {'Nutzer' if app_type == '-3' else 'System'}-Apps"):
                app_info = future.result()
                if app_type == "-3":
                    user_apps.append(app_info)
                else:
                    system_apps.append(app_info)
    
    user_apps.sort(key=lambda x: x["has_background_perm"], reverse=True)
    system_apps.sort(key=lambda x: x["has_background_perm"], reverse=True)
    
    return user_apps, system_apps

def display_apps(apps, title):
    print(f"\n{title}:")
    for i, app in enumerate(apps, 1):
        perms = app['permissions']
        status = "R" if perms['RUN_IN_BACKGROUND'] else "-"
        alarm = "A" if perms['SCHEDULE_EXACT_ALARM'] else "-"
        location = "L" if perms['ACCESS_BACKGROUND_LOCATION'] else "-"
        
        print(f"{i}. [{status}{alarm}{location}] {app['name']} ({app['package']})")

def toggle_permission(package, permission):
    current_state = get_app_permissions(package)[permission]
    action = "revoke" if current_state else "grant"
    run_adb_command(["shell", "pm", action, package, f"android.permission.{permission}"])
    print(f"{'Entzogen' if current_state else 'Erteilt'} {permission} für {package}")

def toggle_all_permissions(package, grant=True):
    permissions = ["RUN_IN_BACKGROUND", "SCHEDULE_EXACT_ALARM", "ACCESS_BACKGROUND_LOCATION"]
    action = "grant" if grant else "revoke"
    for perm in permissions:
        run_adb_command(["shell", "pm", action, package, f"android.permission.{perm}"])
    print(f"Alle Hintergrund-Berechtigungen {'erteilt' if grant else 'entzogen'} für {package}")

def display_legend():
    print("\nLegende der Berechtigungen:")
    print("R - RUN_IN_BACKGROUND: Erlaubt der App, im Hintergrund zu laufen")
    print("A - SCHEDULE_EXACT_ALARM: Erlaubt der App, präzise Alarme zu setzen")
    print("L - ACCESS_BACKGROUND_LOCATION: Erlaubt der App Zugriff auf den Standort im Hintergrund")
    print("\nEinfluss auf das App-Verhalten:")
    print("R: Apps können im Hintergrund aktiv bleiben und Aufgaben ausführen")
    print("A: Apps können auch im Ruhezustand exakte Zeitpläne einhalten")
    print("L: Apps können den Standort verfolgen, auch wenn sie nicht aktiv genutzt werden")
    print("\nHinweis: Das Entziehen dieser Berechtigungen kann die Funktionalität einschränken,")
    print("aber auch Akku und Datenvolumen sparen sowie die Privatsphäre schützen.")

def main():
    print("Verbindung zum Android-Gerät wird hergestellt...")
    run_adb_command(["devices"])
    
    user_apps, system_apps = get_installed_apps()
    
    while True:
        display_apps(user_apps, "Nutzer-Apps")
        display_apps(system_apps, "System-Apps")
        display_legend()
        
        print("\nOptionen:")
        print("1. Berechtigungen ändern")
        print("2. Aktualisieren")
        print("3. Beenden")
        
        choice = input("Wählen Sie eine Option (1-3): ")
        
        if choice == '1':
            app_type = input("Wählen Sie den App-Typ (u für Nutzer-Apps, s für System-Apps): ").lower()
            if app_type not in ['u', 's']:
                print("Ungültige Auswahl. Bitte versuchen Sie es erneut.")
                continue
            
            apps = user_apps if app_type == 'u' else system_apps
            selections = input("Geben Sie die Nummern der Apps ein (durch Kommas getrennt): ").split(',')
            
            for selection in tqdm(selections, desc="Verarbeite Auswahlen"):
                parts = selection.strip().split()
                app_num = int(parts[0]) - 1
                app = apps[app_num]
                
                if len(parts) == 1:
                    action = input(f"Möchten Sie alle Berechtigungen für {app['name']} erteilen (g) oder entziehen (r)? ").lower()
                    if action == 'g':
                        toggle_all_permissions(app['package'], grant=True)
                    elif action == 'r':
                        toggle_all_permissions(app['package'], grant=False)
                    else:
                        print("Ungültige Aktion.")
                else:
                    for perm in parts[1:]:
                        if perm.upper() == 'R':
                            toggle_permission(app['package'], 'RUN_IN_BACKGROUND')
                        elif perm.upper() == 'A':
                            toggle_permission(app['package'], 'SCHEDULE_EXACT_ALARM')
                        elif perm.upper() == 'L':
                            toggle_permission(app['package'], 'ACCESS_BACKGROUND_LOCATION')
                        else:
                            print(f"Ungültige Berechtigung: {perm}")
            
            print("Aktualisiere App-Liste...")
            user_apps, system_apps = get_installed_apps()
        elif choice == '2':
            print("Aktualisiere App-Liste...")
            user_apps, system_apps = get_installed_apps()
        elif choice == '3':
            print("Programm wird beendet.")
            break
        else:
            print("Ungültige Auswahl. Bitte versuchen Sie es erneut.")

if __name__ == "__main__":
    main()
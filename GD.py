import os
import json
import sys
import subprocess

# --- Auto-instalador de dependencias ---
REQUIRED = ["requests", "colorama"]
for package in REQUIRED:
    try:
        __import__(package)
    except ImportError:
        print(f"Instalando dependencia faltante: {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

import requests
from colorama import Fore, Style, init

init(autoreset=True)

# --- CONFIGURACIÓN ---
FILE_NAME = "gd_progress.json"
API_URL = "https://gdbrowser.com/api/level/"

OFFICIAL_LEVELS = {
    "Base after Base": "hard",
    "Blast Processing": "harder",
    "Cant Let Go": "hard",
    "Clutterfunk": "insane",
    "Clubstep": "easy demon",
    "Cycles": "harder",
    "Dash": "insane",
    "Deadlocked": "easy demon",
    "Dry Out": "normal",
    "Electrodynamix": "insane",
    "Electroman Adventures": "insane",
    "Fingerdash": "insane",
    "Geometrical Dominator": "harder",
    "Hexagon Force": "insane",
    "Jumper": "harder",
    "Polargeist": "normal",
    "Stereo Madness": "easy",
    "Theory of Everything": "insane",
    "Theory of Everything 2": "easy demon",
    "Time Machine": "harder",
    "xStep": "insane",
    "Back on Track": "easy"
}

# --- FUNCIONES BASE ---
def load_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(Fore.RED + "⚠ Archivo dañado, se regenerará uno nuevo.")
    data = {
        "official_levels": {name: {"difficulty": diff, "completed": False} for name, diff in OFFICIAL_LEVELS.items()},
        "custom_levels": [],
        "completed_levels": [],
        "demon_counter": {"easy": 0, "medium": 0, "hard": 0, "insane": 0, "extreme": 0}
    }
    save_data(data)
    return data

def save_data(data):
    with open(FILE_NAME, "w") as f:
        json.dump(data, f, indent=4)

# --- UTILIDADES ---
def green(t): return Fore.GREEN + t + Style.RESET_ALL
def red(t): return Fore.RED + t + Style.RESET_ALL
def yellow(t): return Fore.YELLOW + t + Style.RESET_ALL
def blue(t): return Fore.CYAN + t + Style.RESET_ALL

def barra_progreso(porcentaje, largo=20):
    completos = int((porcentaje/100)*largo)
    vacios = largo - completos
    return "[" + "█"*completos + "░"*vacios + f"] {porcentaje:.1f}%"

# --- MENÚ ---
def show_menu():
    print(blue("\n=== GEOMETRY DASH PROGRESS TRACKER ==="))
    print("1. Ver niveles oficiales")
    print("2. Marcar nivel como completado")
    print("3. Añadir nivel que quieres pasar")
    print("4. Ver niveles pendientes")
    print("5. Mover nivel a completados")
    print("6. Eliminar nivel personalizado")
    print("7. Ver demon counter")
    print("8. Ver estadísticas de progreso")
    print("9. Buscar nivel por ID (GD Browser)")
    print("10. Sincronizar niveles personalizados")
    print("0. Salir")

# --- DUPLICADOS ---
def seleccionar_nivel(lista):
    if len(lista) == 1:
        return lista[0]
    print(yellow("⚠ Se encontraron varios niveles con el mismo nombre:"))
    for i, lvl in enumerate(lista, 1):
        extra = f"ID: {lvl.get('id','sin ID')} | Autor: {lvl.get('author','-')} | Stars: {lvl.get('stars','-')}"
        print(f"{i}. {lvl['name']} ({lvl['difficulty']}) | {extra}")
    sel = input("Selecciona el número o escribe el ID: ").strip()
    if sel.isdigit():
        idx = int(sel)-1
        if 0 <= idx < len(lista):
            return lista[idx]
    for lvl in lista:
        if lvl.get("id") == sel:
            return lvl
    print(red("❌ Selección inválida."))
    return None

def seleccionar_custom(data, prompt="Nombre o ID: "):
    name = input(prompt).strip()
    # Primero por ID
    for lvl in data["custom_levels"]:
        if lvl.get("id") == name:
            return lvl
    # Por nombre
    matches = [lvl for lvl in data["custom_levels"] if lvl["name"].lower() == name.lower()]
    if matches:
        return seleccionar_nivel(matches)
    print(red("❌ Nivel no encontrado."))
    return None

# --- FUNCIONES PRINCIPALES ---
def mark_completed(data):
    print(blue("\n--- Marcar nivel como completado ---"))
    lvl = seleccionar_custom(data)
    if lvl:
        data["completed_levels"].append(lvl)
        if lvl["is_demon"]:
            demon_type = lvl["difficulty"].split()[0]
            data["demon_counter"][demon_type] += 1
        data["custom_levels"].remove(lvl)
        save_data(data)
        print(green(f"✔ '{lvl['name']}' completado."))
        return
    # Oficiales
    name = input("Si es nivel oficial, escribe su nombre: ").strip()
    if name in data["official_levels"]:
        lvl_info = data["official_levels"][name]
        if not lvl_info["completed"]:
            lvl_info["completed"] = True
            if "demon" in lvl_info["difficulty"]:
                data["demon_counter"]["easy"] += 1
            save_data(data)
            print(green(f"✔ Nivel oficial '{name}' completado."))
        else:
            print(yellow("⚠ Ya estaba completado."))

def add_custom_level(data):
    print(blue("\n--- Añadir nivel personalizado ---"))
    level_id = input("Introduce el ID del nivel (deja vacío para manual): ").strip()
    if level_id:
        # Sincroniza automáticamente desde GD Browser
        try:
            resp = requests.get(API_URL + level_id)
            info = resp.json()
            if "error" in info:
                return print(red("❌ Nivel no encontrado."))
            diff = info["difficulty"].lower()
            is_demon = "demon" in diff
            new_lvl = {
                "name": info["name"],
                "difficulty": diff,
                "is_demon": is_demon,
                "id": str(info["id"]),
                "author": info["author"],
                "stars": info["stars"]
            }
            data["custom_levels"].append(new_lvl)
            save_data(data)
            print(green(f"✔ Nivel '{info['name']}' sincronizado y añadido automáticamente."))
            return
        except Exception as e:
            print(red(f"❌ Error al sincronizar: {e}"))
            return
    # Modo manual
    name = input("Nombre del nivel: ")
    diff = input("Dificultad (easy, normal, hard, harder, insane, demon): ").lower()
    if diff == "demon":
        demon_type = input("Tipo de demon (easy, medium, hard, insane, extreme): ").lower()
        diff = demon_type + " demon"
        is_demon = True
    else:
        is_demon = False
    lvl_data = {"name": name, "difficulty": diff, "is_demon": is_demon}
    data["custom_levels"].append(lvl_data)
    save_data(data)
    print(green(f"✔ Nivel '{name}' añadido manualmente."))

def view_pending_levels(data):
    print(blue("\n--- Niveles pendientes ---"))
    if not data["custom_levels"]:
        return print(yellow("No tienes niveles pendientes."))
    for lvl in data["custom_levels"]:
        print(f"- {lvl['name']} ({lvl['difficulty']}) [ID: {lvl.get('id','sin ID')}]")

def move_to_completed(data):
    print(blue("\n--- Mover nivel a completados ---"))
    lvl = seleccionar_custom(data)
    if lvl:
        data["completed_levels"].append(lvl)
        if lvl["is_demon"]:
            demon_type = lvl["difficulty"].split()[0]
            data["demon_counter"][demon_type] += 1
        data["custom_levels"].remove(lvl)
        save_data(data)
        print(green(f"✔ '{lvl['name']}' movido a completados."))

def delete_custom_level(data):
    print(blue("\n--- Eliminar nivel personalizado ---"))
    lvl = seleccionar_custom(data)
    if lvl:
        data["custom_levels"].remove(lvl)
        save_data(data)
        print(green(f"✔ Nivel '{lvl['name']}' eliminado."))

def show_statistics(data):
    print(blue("\n--- Estadísticas ---"))
    total_off = len(data["official_levels"])
    done_off = sum(1 for l in data["official_levels"].values() if l["completed"])
    total_cus = len(data["custom_levels"]) + len(data["completed_levels"])
    done_cus = len(data["completed_levels"])
    def pct(a,b): return 0 if b==0 else a/b*100
    print(f"Oficiales: {done_off}/{total_off} {barra_progreso(pct(done_off,total_off))}")
    print(f"Custom: {done_cus}/{total_cus} {barra_progreso(pct(done_cus,total_cus))}")
    total = total_off + total_cus
    done = done_off + done_cus
    print(f"Total: {done}/{total} {barra_progreso(pct(done,total))}")

def show_demon_counter(data):
    print(blue("\n--- Demon Counter ---"))
    total = sum(data["demon_counter"].values())
    for k, v in data["demon_counter"].items():
        print(f"{k.title()} Demons: {v}")
    print(blue(f"Total Demons: {total}"))

def buscar_nivel_por_id(_):
    level_id = input("Introduce el ID: ").strip()
    if not level_id: return print(red("❌ ID inválido."))
    try:
        resp = requests.get(API_URL + level_id)
        info = resp.json()
        if "error" in info: return print(red("❌ Nivel no encontrado."))
        print(blue("\n=== Información del nivel ==="))
        for k in ["name","author","difficulty","stars","orbs","length","downloads"]:
            print(f"{k.title()}: {info[k]}")
    except Exception as e:
        print(red(f"Error: {e}"))

def sincronizar_niveles(data):
    todos = data["custom_levels"] + data["completed_levels"]
    if not todos: return print(yellow("No hay niveles personalizados."))
    for lvl in todos:
        if "id" not in lvl:
            print(yellow(f"{lvl['name']} no tiene ID."))
            new = input("Añadir ID? (vacío=omitir): ").strip()
            if new: lvl["id"]=new
            else: continue
        try:
            r=requests.get(API_URL+str(lvl["id"]))
            info=r.json()
            if "error" in info: 
                print(red(f"Nivel {lvl['id']} no encontrado."))
                continue
            lvl["name"]=info["name"]
            lvl["difficulty"]=info["difficulty"].lower()
            lvl["is_demon"]="demon" in lvl["difficulty"]
            lvl["author"]=info["author"]
            lvl["stars"]=info["stars"]
            print(green(f"✔ {lvl['name']} sincronizado."))
        except Exception as e:
            print(red(f"Error: {e}"))
    save_data(data)
    print(blue("\nSincronización completada ✅"))

# --- MAIN ---
def main():
    data = load_data()
    while True:
        show_menu()
        op = input("Opción: ").strip()
        if op=="1":
            for lvl, info in data["official_levels"].items():
                print(f"{lvl} - {'✅' if info['completed'] else '❌'} ({info['difficulty']})")
        elif op=="2": mark_completed(data)
        elif op=="3": add_custom_level(data)
        elif op=="4": view_pending_levels(data)
        elif op=="5": move_to_completed(data)
        elif op=="6": delete_custom_level(data)
        elif op=="7": show_demon_counter(data)
        elif op=="8": show_statistics(data)
        elif op=="9": buscar_nivel_por_id(data)
        elif op=="10": sincronizar_niveles(data)
        elif op=="0":
            print(blue("👋 Saliendo..."))
            break
        else: print(red("❌ Opción inválida."))

if __name__=="__main__":
    main()

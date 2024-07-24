import os
import re
import json
import random
import string
import shutil
import locale
import argparse
import subprocess
import sys
import getpass
import xml.etree.ElementTree as ET
from tqdm import tqdm

def run_with_elevated_privileges(command):
    if sys.platform.startswith('win'):
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin() == 0:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)
    else:
        if os.geteuid() != 0:
            sudo_password = getpass.getpass("[sudo] Passwort für %s: " % getpass.getuser())
            command = ['sudo', '-S'] + command
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            proc.communicate(sudo_password + '\n')
            return proc.returncode
    return subprocess.call(command)

def ensure_permissions(path):
    try:
        if not os.access(path, os.W_OK):
            if sys.platform.startswith('win'):
                run_with_elevated_privileges(['icacls', path, '/grant', f'{os.getenv("USERNAME")}:F'])
            else:
                run_with_elevated_privileges(['chmod', '-R', '777', path])
    except Exception as e:
        print(f"Failed to set permissions: {e}")
        sys.exit(1)

class CSharpObfuscator:
    def __init__(self, language=None):
        self.obfuscation_map = {}
        self.string_map = {}
        self.file_map = {}
        self.namespace_map = {}
        self.external_classes = set()
        self.lang = self.load_language(language)

    def load_language(self, language=None):
        if language:
            lang_code = language
        else:
            lang_code = locale.getdefaultlocale()[0][:2]

        script_dir = os.path.dirname(os.path.abspath(__file__))
        lang_file = os.path.join(script_dir, f'language_{lang_code}.json')

        if not os.path.exists(lang_file):
            lang_file = os.path.join(script_dir, 'language_en.json')

        with open(lang_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def obfuscate_name(self, name):
        if name not in self.obfuscation_map:
            self.obfuscation_map[name] = ''.join(random.choices(string.ascii_letters, k=10))
        return self.obfuscation_map[name]

    def obfuscate_string(self, string):
        if string not in self.string_map:
            self.string_map[string] = ''.join(random.choices(string.ascii_letters, k=len(string)))
        return self.string_map[string]

    def obfuscate_filename(self, filename):
        name, ext = os.path.splitext(filename)
        if name not in self.file_map:
            self.file_map[name] = ''.join(random.choices(string.ascii_letters, k=10))
        return f"{self.file_map[name]}{ext}"

    def remove_comments(self, content):
        content = re.sub(r'//.*', '', content)
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        return content

    def find_external_classes(self, content):
        using_statements = re.findall(r'using\s+([^;]+);', content)
        for statement in using_statements:
            self.external_classes.add(statement.strip().split('.')[-1])

    def obfuscate_code(self, content):
        content = self.remove_comments(content)
        self.find_external_classes(content)

        # Obfuscate namespaces
        for match in re.finditer(r'\bnamespace\s+([a-zA-Z_][\w.]*)', content):
            old_namespace = match.group(1)
            new_namespace = self.obfuscate_name(old_namespace)
            self.namespace_map[old_namespace] = new_namespace
            content = content.replace(f"namespace {old_namespace}", f"namespace {new_namespace}")

        # Obfuscate class names, method names, and variable names
        for match in re.finditer(r'\b(class|struct|enum|interface|void|int|string|bool|float|double|decimal|char|byte|sbyte|short|ushort|uint|long|ulong)\s+([a-zA-Z_]\w*)', content):
            old_name = match.group(2)
            if old_name not in self.external_classes:
                new_name = self.obfuscate_name(old_name)
                content = re.sub(r'\b' + old_name + r'\b', new_name, content)

        # Obfuscate string contents
        content = re.sub(r'"([^"\\]*(?:\\.[^"\\]*)*)"', lambda m: f'"{self.obfuscate_string(m.group(1))}"', content)

        return content

    def obfuscate_file(self, file_path, output_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        obfuscated_content = self.obfuscate_code(content)

        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(obfuscated_content)

        print(f"Obfuscated: {file_path} -> {output_path}")

    def update_project_files(self, output_path):
        for root, dirs, files in os.walk(output_path):
            for file in files:
                if file.endswith('.sln'):
                    self.update_sln_file(os.path.join(root, file))
                elif file.endswith('.csproj'):
                    self.update_csproj_file(os.path.join(root, file))
                elif file == 'AssemblyInfo.cs':
                    self.update_assembly_info(os.path.join(root, file))

    def update_sln_file(self, sln_path):
        with open(sln_path, 'r', encoding='utf-8') as file:
            content = file.read()

        for old_name, new_name in self.file_map.items():
            content = content.replace(f"{old_name}.csproj", f"{new_name}.csproj")

        with open(sln_path, 'w', encoding='utf-8') as file:
            file.write(content)

        print(f"Updated SLN file: {sln_path}")

    def update_csproj_file(self, csproj_path):
        tree = ET.parse(csproj_path)
        root = tree.getroot()

        for compile_element in root.findall(".//Compile"):
            include = compile_element.get('Include')
            if include:
                old_name = os.path.splitext(include)[0]
                if old_name in self.file_map:
                    new_name = self.file_map[old_name]
                    compile_element.set('Include', f"{new_name}.cs")

        tree.write(csproj_path, encoding='utf-8', xml_declaration=True)
        print(f"Updated CSPROJ file: {csproj_path}")

    def update_assembly_info(self, assembly_info_path):
        with open(assembly_info_path, 'r', encoding='utf-8') as file:
            content = file.read()

        for old_namespace, new_namespace in self.namespace_map.items():
            content = content.replace(old_namespace, new_namespace)

        with open(assembly_info_path, 'w', encoding='utf-8') as file:
            file.write(content)

        print(f"Updated AssemblyInfo.cs: {assembly_info_path}")

    def obfuscate_project(self, project_path):
        project_path = os.path.abspath(project_path.strip())
        if not os.path.exists(project_path):
            raise FileNotFoundError(f"The directory does not exist: {project_path}")
        
        project_name = os.path.basename(project_path)
        parent_dir = os.path.dirname(project_path)
        output_path = os.path.join(parent_dir, f"{project_name}_Obfuscated")
        
        if os.path.exists(output_path):
            shutil.rmtree(output_path)
        shutil.copytree(project_path, output_path)
        
        for root, dirs, files in os.walk(output_path):
            for file in tqdm(files, desc=self.lang['obfuscating_files']):
                if file.endswith('.cs'):
                    file_path = os.path.join(root, file)
                    new_filename = self.obfuscate_filename(file)
                    new_file_path = os.path.join(root, new_filename)
                    os.rename(file_path, new_file_path)
                    self.obfuscate_file(new_file_path, new_file_path)

        self.update_project_files(output_path)

        # Save obfuscation map
        with open(os.path.join(output_path, "obfuscation_map.json"), 'w', encoding='utf-8') as f:
            json.dump({
                "obfuscation_map": self.obfuscation_map,
                "string_map": self.string_map,
                "file_map": self.file_map,
                "namespace_map": self.namespace_map
            }, f, indent=2, ensure_ascii=False)

    def deobfuscate_project(self, obfuscated_path, output_path):
        obfuscated_path = os.path.abspath(obfuscated_path)
        output_path = os.path.abspath(output_path)
        obfuscation_map_path = os.path.join(obfuscated_path, "obfuscation_map.json")

        with open(obfuscation_map_path, 'r', encoding='utf-8') as f:
            obfuscation_data = json.load(f)
            self.obfuscation_map = {v: k for k, v in obfuscation_data["obfuscation_map"].items()}
            self.string_map = {v: k for k, v in obfuscation_data["string_map"].items()}
            self.file_map = {v: k for k, v in obfuscation_data["file_map"].items()}
            self.namespace_map = {v: k for k, v in obfuscation_data["namespace_map"].items()}

        if os.path.exists(output_path):
            shutil.rmtree(output_path)
        shutil.copytree(obfuscated_path, output_path)

        for root, dirs, files in os.walk(output_path):
            for file in tqdm(files, desc=self.lang['deobfuscating_files']):
                file_path = os.path.join(root, file)
                
                if file.endswith('.cs') or file in ['AssemblyInfo.cs'] or file.endswith(('.sln', '.csproj')):
                    self.deobfuscate_file(file_path, file_path)
                    
                    if file.endswith('.cs'):
                        original_filename = self.file_map.get(os.path.splitext(file)[0], file)
                        new_file_path = os.path.join(root, original_filename)
                        os.rename(file_path, new_file_path)

        self.update_project_files(output_path)

    def deobfuscate_file(self, file_path, output_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        for obfuscated, original in self.obfuscation_map.items():
            content = re.sub(r'\b' + obfuscated + r'\b', original, content)

        for obfuscated, original in self.string_map.items():
            content = content.replace(f'"{obfuscated}"', f'"{original}"')

        for obfuscated, original in self.namespace_map.items():
            content = content.replace(obfuscated, original)

        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)

        print(f"Deobfuscated: {file_path} -> {output_path}")

def main():
    parser = argparse.ArgumentParser(description='C# Code Obfuscator/Deobfuscator')
    parser.add_argument('-lang', choices=['en', 'de'], help='Language for the program (en or de)')
    args = parser.parse_args()

    obfuscator = CSharpObfuscator(args.lang)

    while True:
        choice = input(obfuscator.lang['menu_prompt'])

        if choice == 'q':
            break
        elif choice == '1':
            project_path = input(obfuscator.lang['enter_project_path'])
            project_path = project_path.strip().strip('"')
            if not os.path.exists(project_path):
                print(f"Error: The directory does not exist: {project_path}")
                continue
            try:
                ensure_permissions(project_path)
                obfuscator.obfuscate_project(project_path)
                print(obfuscator.lang['obfuscation_complete'].format(f"{project_path}_Obfuscated"))
            except Exception as e:
                print(f"An error occurred: {str(e)}")
        elif choice == '2':
            obfuscated_path = input(obfuscator.lang['enter_obfuscated_path'])
            obfuscated_path = obfuscated_path.strip().strip('"')
            if not os.path.exists(obfuscated_path):
                print(f"Error: The directory does not exist: {obfuscated_path}")
                continue
            output_path = obfuscated_path.replace("_Obfuscated", "_Deobfuscated")
            try:
                ensure_permissions(obfuscated_path)
                ensure_permissions(os.path.dirname(output_path))
                obfuscator.deobfuscate_project(obfuscated_path, output_path)
                print(obfuscator.lang['deobfuscation_complete'].format(output_path))
            except Exception as e:
                print(f"An error occurred: {str(e)}")
        else:
            print(obfuscator.lang['invalid_choice'])

if __name__ == "__main__":
    main()
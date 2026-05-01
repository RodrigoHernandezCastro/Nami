import os
import fnmatch
from pathlib import Path

class TreeGenerator:
    def __init__(self, root_dir, output_file="proyecto_estructura.txt"):
        self.root_dir = Path(root_dir)
        self.output_file = output_file
        self.tree = []
        self.ignore_patterns = self._load_gitignore()
        
        # Siempre ignoramos la carpeta .git por defecto para no saturar el árbol
        self.ignore_patterns.add('.git')

    def _load_gitignore(self):
        """Lee el archivo .gitignore y extrae los patrones a ignorar."""
        patterns = set()
        gitignore_path = self.root_dir / '.gitignore'
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Ignorar líneas vacías, comentarios (#) o marcadores de conflicto de Git (<, =, >)
                    if not line or line.startswith(('#', '<', '=', '>')):
                        continue
                    
                    # Quitar el slash final '/' para que fnmatch evalúe el nombre de la carpeta correctamente
                    if line.endswith('/'):
                        line = line[:-1]
                        
                    patterns.add(line)
        return patterns

    def _should_ignore(self, path: Path):
        """Verifica si el archivo o carpeta actual coincide con algún patrón del .gitignore."""
        for pattern in self.ignore_patterns:
            # fnmatch permite evaluar comodines como *.log de forma nativa
            if fnmatch.fnmatch(path.name, pattern):
                return True
        return False

    def build_tree(self, path, prefix=""):
        # Filtramos el contenido usando la función _should_ignore
        contents = [p for p in path.iterdir() if not self._should_ignore(p)]
        
        # Ordenamos: primero directorios, luego archivos (alfabéticamente)
        contents = sorted(contents, key=lambda x: (not x.is_dir(), x.name.lower()))
        
        pointers = ["├── "] * (len(contents) - 1) + ["└── "]
        
        for pointer, item in zip(pointers, contents):
            # Añadimos la línea al árbol
            self.tree.append(f"{prefix}{pointer}{item.name}")
            
            # Si es un directorio, bajamos recursivamente
            if item.is_dir():
                extension = "│   " if pointer == "├── " else "    "
                self.build_tree(item, prefix=prefix + extension)

    def save(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(f"{self.root_dir.name}/\n")
            f.write("\n".join(self.tree))
        print(f"✅ Estructura guardada con éxito en: {self.output_file}")

if __name__ == "__main__":
    # Ejecuta el generador en el directorio actual
    generator = TreeGenerator(".")
    generator.build_tree(generator.root_dir)
    generator.save()
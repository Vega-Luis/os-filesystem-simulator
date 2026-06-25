# Guía de pruebas — OS File System Simulator

Marca cada casilla mientras pruebas. Si algo falla, anota el error exacto
(captura de pantalla o el texto del error) antes de seguir al siguiente paso.

## 0. Antes de empezar

```bash
cd ProyectoFinal
python main.py
```

- [ ] Aparece el diálogo **"CREATE — Crear disco virtual"** antes que cualquier otra ventana
- [ ] Tiene dos campos: cantidad de sectores y tamaño de sector, con valores por defecto (200 y 64)
- [ ] Al cambiar los números, la línea "Tamaño total del disco" se actualiza sola

**Prueba A — cancelar:**
- [ ] Click en "Salir" → el programa se cierra sin abrir la ventana principal (no debe quedar nada abierto ni dar error en consola)

Vuelve a correr `python main.py` para continuar.

**Prueba B — crear con valores personalizados:**
- [ ] Cambia a, por ejemplo, 50 sectores y 32 bytes
- [ ] Click en "Crear disco" → el diálogo se cierra y se abre la ventana principal (una sola ventana, no dos)
- [ ] La ventana principal muestra "Ruta actual: /" y el TREE muestra solo `root/`

---

## 1. Crear carpetas y archivos (MKDIR / FILE)

- [ ] Click en **MKDIR**, escribe `Documentos`, acepta
  → aparece `📁 Documentos` en la tabla derecha y en el TREE
- [ ] Click en **MKDIR** otra vez, escribe `Documentos` de nuevo (el mismo nombre)
  → debe preguntarte si deseas sobrescribir (no debe crear un duplicado silenciosamente)
- [ ] Click en **FILE**, nombre `nota.txt`, contenido `hola mundo`, acepta
  → aparece `📄 nota.txt` con un tamaño en bytes mayor a 0

---

## 2. Navegación (CambiarDIR / Subir / doble click)

- [ ] Doble click sobre la fila `Documentos` en la tabla
  → "Ruta actual" cambia a `/Documentos`, la tabla queda vacía (está recién creada)
- [ ] Click en **Subir (..)**
  → vuelves a `/`, y ves de nuevo `Documentos` y `nota.txt`
- [ ] Click en **CambiarDIR**, escribe `Documentos`, acepta
  → mismo resultado que el doble click

---

## 3. Ver información (VerPropiedades / VerFile)

- [ ] Click simple para **seleccionar** la fila `nota.txt` (debe quedar resaltada)
- [ ] Click en **VerPropiedades**
  → ventana con nombre, extensión (`txt`), fechas, tamaño
- [ ] Click en **VerFile** (con `nota.txt` aún seleccionado)
  → ventana mostrando el contenido exacto: `hola mundo`

**Prueba de error esperado:**
- [ ] Sin seleccionar nada en la tabla, click en **VerPropiedades**
  → debe pedirte que selecciones algo primero, no debe crashear

---

## 4. Modificar (ModFILE)

- [ ] Selecciona `nota.txt`, click en **ModFILE**
  → se abre con el contenido actual ya cargado (`hola mundo`)
- [ ] Cambia el texto a `contenido modificado`, acepta
- [ ] Click en **VerFile** de nuevo sobre `nota.txt`
  → debe mostrar `contenido modificado`, no el texto viejo

---

## 5. Mover / renombrar (MoVer)

- [ ] Click en **MoVer**, origen `nota.txt`, destino `notas.txt` (sin `/`)
  → en la tabla, `nota.txt` desaparece y aparece `notas.txt` (esto es un rename)
- [ ] Click en **MoVer** otra vez, origen `notas.txt`, destino `/Documentos/notas.txt`
  → `notas.txt` desaparece de la raíz; entra a `Documentos` (doble click) y debe estar ahí

---

## 6. Buscar (FIND)

- [ ] Vuelve a la raíz (`Subir (..)` si hace falta)
- [ ] Click en **FIND**, escribe `*.txt`, acepta
  → debe listarte la ruta completa de `notas.txt` dentro de `/Documentos`

---

## 7. Copiar — las 3 variantes (CoPY)

**Primero crea un archivo de prueba real en tu computadora** (fuera del proyecto), por ejemplo en el Escritorio: `prueba_real.txt` con el texto `contenido desde Windows`.

- [ ] Click en **CoPY**, selecciona la opción **"De mi computadora (real) → al File System virtual"**
- [ ] Click en "Elegir..." junto a Origen → se abre el explorador de Windows
- [ ] Selecciona `prueba_real.txt`, acepta el diálogo de CoPY
  → debe aparecer `prueba_real.txt` en tu file system virtual (en la carpeta donde estabas parado)
- [ ] Selecciónalo y dale **VerFile** → debe decir `contenido desde Windows`

- [ ] Click en **CoPY** de nuevo, esta vez **"Del File System virtual → a mi computadora (real)"**
- [ ] Origen: escribe `prueba_real.txt`
- [ ] Click en "Elegir..." junto a Destino → se abre "Guardar como" de Windows, elige una ubicación (ej. Escritorio, nombre `copia_de_vuelta.txt`)
  → abre ese archivo en el explorador de Windows después y confirma que tiene el mismo contenido

- [ ] Click en **CoPY** una vez más, **"Dentro del File System virtual (virtual → virtual)"**
- [ ] Origen: `prueba_real.txt`, Destino: `/Documentos`
  → entra a `/Documentos` y confirma que el archivo está ahí también, sin que se haya borrado el original en la raíz

**Caso de error esperado — archivo no de texto:**
- [ ] Intenta copiar una imagen `.jpg` o `.png` real a virtual
  → debe darte un mensaje de error claro diciendo que no soporta archivos binarios, NO debe crashear el programa

---

## 8. Eliminar (ReMove)

- [ ] Selecciona `prueba_real.txt` en la raíz, click en **ReMove**
  → debe desaparecer de la tabla sin pedir confirmación (es un archivo, no un directorio con contenido)
- [ ] Selecciona la carpeta `Documentos` (que ya tiene archivos dentro), click en **ReMove**
  → debe preguntarte si deseas borrar de forma recursiva (porque no está vacía)
- [ ] Acepta el borrado recursivo
  → `Documentos` y todo su contenido deben desaparecer del TREE y de la tabla

---

## 9. Disco lleno

Esto es más fácil de provocar si en el paso 0 creaste el disco con pocos sectores (ej. 5 sectores de 8 bytes = 40 bytes totales).

- [ ] Con un disco pequeño, intenta crear un archivo con mucho contenido (varios párrafos de texto)
  → debe darte un mensaje claro de "disco lleno", NO debe crashear ni quedar a medias

---

## 10. Cerrar y volver a abrir (persistencia del disco)

- [ ] Cierra la ventana completamente (la X)
- [ ] Verifica en la carpeta `disk/` que el archivo `virtual_disk.bin` sigue existiendo (no se borró)
- [ ] Corre `python main.py` de nuevo
  → el diálogo de CREATE debe avisarte que ya existe un disco previo y que se usará su tamaño original
- [ ] Nota esperada (y esto es importante explicarlo en la documentación): el **file system en memoria se pierde** al cerrar — es decir, las carpetas/archivos que creaste antes de cerrar NO van a aparecer en el árbol al reabrir, aunque el archivo `.bin` siga existiendo en disco. Esto es el comportamiento que pide el enunciado explícitamente ("cuando la aplicación termina se pierde el file System, sin embargo, no deben eliminar el archivo que representa el disco").

---

## Qué hacer con los resultados

Por cada casilla que **no** se cumpla, anota:
1. En qué paso exacto pasó
2. Qué esperabas vs qué pasó de verdad
3. Si salió un error en la consola (la ventana negra detrás), copia el texto completo del traceback

Con eso puedo corregir exactamente lo que falle, en vez de adivinar.

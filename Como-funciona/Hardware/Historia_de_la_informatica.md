

-------------------------------------------------------------------
# 1960s

### Olivetti Programma 101
Es el primer ordenador(calculadora) comercial, fabricado por Olivetti en el 64. Se programaba con tecnología de cintas magneticas. 
No tenia grafica sino que se comunicaba con luces y te imprimia en papel el resultado de las cuentas.


-------------------------------------------------------------------
# 1970s

### Altair 8080 - 1975
Ordenador modular DIY (se compraba el kit (ampliable) y se montaba con amplios conocimientos en electronica). No tenia pantalla sino botones y palancas
para entrada de datos y leds para salida.
Especificaciones -> 2 mhz y 8bits.
- Puerto serie -> intermcabio de datos unidireccional
- Puerto paralelo -> intermcabio de datos bidireccional

### Lenguaje Basic 1975
Creado por Bill Gates y Paul Allen

-------------------------------------------------------------------
# 1980s

### Puerto ISA - 1981
Puerto ISA -> de 8 a 16 bits. Estandar de conexión.   

### Estandar MDA - 1981
Estaba pensado para monitores CRT de fosoforo verde monocromo. Había 4KB de memoria de video para imprimir 80 caracteres en pantalla y un chip ROM
de 8Kb para almacenar 437 caracteres. 720×350 de resolucion.
- **IBM MDA** -> Chip motorola 6845. Puertos: impresora, monitor y bus ISA. Tambien un reloj para sincronizar los ciclos con la CPU.   

### Estandar CGA - 1981
VRAM de 16Kb para poder mostrar 16 colores (320x200) o 4 (640x200).
- **Hercules Graphics Card - 1982** -> 720 x 350 px de esolucion. Tenia dos ROMs para meter mas caracteres (tailandeses).

### Estandar EGA - 1984
Estándar de IBM Enhanced Graphics Adapter -> colores sin restriccion (16 colores a resolucion 640x350) con el puerto VGA.    
- Puerto ISA -> de 8 a 16 bits. Estandar de conexión.   
- **ATI EGA Wonder 800** -> GPU 10 Mhz, DRAM a 8Mhz. 256 Kb de memoria de video con un bus de 32 bits.

### Windows 1.0 - 1985

### Estandar VGA - 1988
Puerto VGA (15 pines) y sus estándares (min 256 Kb de VRAM) -> Resolucion de 640X480p a 16 colores y 320x200 a 256 colores

### RAMDAC - 1988
Le llega la imagen digital del chip y se la entrega al monitor convertida analógica. Tres convertidores para rojo azul y verde respectivamente

### Estandar SVGA - 1989
IBM saca el estandar XGA 1024x768 pero fracasa.  
Asi que el VESA (video electronic standart assocaition) que saca el SVGA que es igual, con 8 bits de color por pixel (256 colores 16 bits)

-------------------------------------------------------------------
# 1990s

### Puerto PCI - 1992
Es mas pequeño y barato que su antecesor el puerto ISA. Ademas el multipropósito (sirve para poder conectar varios periféricos)

> Año 1995 la explosión del 3D  

### Aceleradora 3D - 1995
Le quitaba trabajo al procesador de decodificacion de video para conseguir mas resolcuion y mejores efectos. 

- **S3 Virge 4MB DRAM** -> procesaba en el mismo chip 2d y 3d. Resolucion de 640x480 y 800x600. 4Md de DRAM. Api S3D. Era un poco chusta porque iba peor que sin ella.

### La guerra de las APIs - 1995
Salieron muchas APIs para tarjetas graficas.
Extintas -> OpenGL(Silicon Graphics - codigo libre), SD3, 3dfX
Continuadas -> DirectX, Vulkan(AMD), Mantle(AMD)

-------------------------------------------------------------------
VBIOS -> donde se almacena el software de arranque de la gráfica antes de que arranque el propio SO  

La DRAM (Dynamic RAM) es la memoria de la tarjeta gráfica. La CPU le manda los datos que ha recibido por el puerto PCI. Guarda texturas y mapas 3d.
Necesita mucho ancho de banda que se lo da el bus y la tasa de refresco. Era muy barata. Es mas lenta que la SRAM o cache.
Cada celda de la memoria tiene un trasnsistor y un capacitor para poder almacenar el 0 y el 1. Unos impulsores recargan por cada ciclo la información
haciendo que no se pierda. Como estos ciclos dependen de que les llegue corriente todo el rato al apagarse se pierde todo, siendo volatil.

Para evitar tener que programar un software para una tarjeta grafica mas un sistema operativo en concreto, y que se supiera comunicar con la gráfica 
(cantidad de pixeles, resolucion, colores). La API era un interprete que podia hacer que un mismo programa funcionara para cualquier grafica.
> Sofftware -> API -> driver de la grafica -> tarjeta gráfica  



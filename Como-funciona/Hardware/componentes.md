
----------------------------------------
# Disco duro

### Tipos de disco duro

HDD -> **hard disk** -> un disco que gira y una aguja magnetica que va escribiendo la informacion en él. Esta dividido en trozitos (pistas magneticas)
y la aguja imanta cada uno dandole un valor magnetico positivo o negativo que equivale a 0 o 1. Es todo mas *analógico*. Suele haber
varios discos/agujas (como un sandwich, alternandose encima unos de otros). Es mas lento que el SDD y resiste peor los golpes.

SDD -> **solid state** -> almacena la informacion de manera electronica (en base a puertas logicas que almacenan un estado "0" u otro "1" ).
No necesita energia para almacenar los datos adiferencia de la volatil memoria RAM. Los pendrives funcionan de esta manera.

Fuentes: \[ [1](https://youtu.be/xBzeiZzYELw), [2](https://youtu.be/fTRxLMJn_Jg) ]

----------------------------------------
### Sistema de archivos. Particiones

El sistema de archivos hace que ordenador almacene datos (archivos, a ser posible ordenados), aaceda a ellos, los borre, mueva,
los recupere y administre quien acceda a ellos (permisos o ACLs).

Un disco duro se puede dividir en particiones.

1. **FAT32** -> sistema obsoleto (no permite archivos mayores que 4gb ni particiones masyores de 8tb). Evoluciono a **EXFAT** 
 
2. **NTFS** -> Es el que utiliza Windows por defecto. (archivos de hasta 16tb). Transaccional y permite cifrado.
Transaccional: los archivos tienen metadatos (informacion como por ejemplo lo que ocupa, la ruta donde esta almacenado, el usaurio propietario...)
Tambien tiene un "diario" que los cambios que se estan realizando en el disco (por ejemplo copiar un archivo) y si se cuelga el sistema de golpe,
gracias al diario, cuando se reinicie, podra continuar y acabar esa tarea pendiente.

3. **EXT4** ->  Sistema utilizado por Linux (el equivalente en caracteristicas al ntfs de windows). Tambien es transaccional y permite archivos de gran
 tamaño.

Fuentes -> [GioCode](https://www.youtube.com/c/giova50000), [redeszone](https://www.redeszone.net/tutoriales/servidores/sistemas-archivos-ext4-btfs-zfs-elegir/)

----------------------------------------
### Fragmentacion de un disco

Un disco duro almacena los datos, pero no lo hace de manera ordenada (o sea no dejando espacio vacio entre donde acaba archivo y empieza el siguiente)
sino que escribe donde primero le pilla.  
Que esté guardado de manera tan random hace que al acceder a un archivo le cueste mas trabajo (ya que esta muy desordenado y pierde tiempo 
leyendo muchos espacios vacios ). Asi que si queremos ordenar, le tenemos que decir que mueva un archivo detras de otro y que deje todo el espacio 
sin usar al final (**desfragmentar**).
```
Desfragmentado -> [Sistema Operativo] [Peliculas] [ Microsoft Office ] [ Documentos ] [ Minecraft ] [  Vacio                       ] 
Fragmentado    -> [Sistema Operativo] [ Vacio ] [ Peliculas ] [ Vacio ] [ Microsoft Office ] [ Documentos ] [ Vacio  ] [ Minecraft ]
```

----------------------------------------
# Tarjeta gráfica
La tarjeta gráfica es como un microprocesador pero que está especializado en operaciones en paralelo, esenciales para los gráficos.


### Puerto de conexión
Las tarjetas gráficas utilizan un puerto para comunicarse con el resto del ordenador.
- Puerto ISA 1981 -> de 8 a 16 bits. 
- Puerto PCI 1992 -> Es mas pequeño y barato que su antecesor el puerto ISA. Ademas el multipropósito (sirve para poder conectar varios periféricos)

### Otras partes

**RAMDAC** Le llega la imagen digital del chip y se la entrega al monitor convertida analógica. Tres convertidores para rojo azul y verde
respectivamente.  
**VBIOS** -> donde se almacena el software de arranque de la gráfica antes de que arranque el propio SO
**Cable SATA** -> cable de once pines que se utilizaba para conectar la grafica al monitor (normalmente de tubo)
La **DRAM** (Dynamic RAM) es la memoria de la tarjeta gráfica. La CPU le manda los datos que ha recibido por el puerto PCI. Guarda texturas y mapas 3d.
Necesita mucho ancho de banda que se lo da el bus y la tasa de refresco. Era muy barata.
**API**
Para evitar tener que programar un software para una tarjeta grafica mas un sistema operativo en concreto, y que se supiera comunicar con la gráfica
(cantidad de pixeles, resolucion, colores). La API era un interprete que podia hacer que un mismo programa funcionara para cualquier grafica.
> Sofftware -> API -> driver de la grafica -> tarjeta gráfica  

---------------------------------------------------
# Memoria RAM

Es mas lenta que la SRAM o cache. Cada celda de la memoria tiene un trasnsistor y un capacitor para poder almacenar el 0 y el 1. Unos impulsores 
recargan por cada ciclo la información haciendo que no se pierda. Como estos ciclos dependen de que les llegue corriente todo el rato al apagarse se
pierde todo, siendo volatil.

---------------------------------------------------
# Sistema Operativo 

### Firmware
El firmware es codigo a muy bajo nivel escrito en una memoria ROM (de solo lectura) de un dispositivo (ejemplo un router) y se encarga de controlar
el funcionamiento del dispositivo, desde su arranque hasta su apagado. Se comunica directamente con el hardware, entre otras cosas para arrancar 
el sistema, para acceder a la memoria, controlar dispositivos de entrada y salida, etc.


### Kernel
Es el nucelo del sistema operativo. El programa madre que soporta al resto, el primero que se carga en memoria. Comunica el hardware y el
software y se encarga de coordinar la ejecución de los programas y gestionar los procesos.

### DLL
Las bibliotecas compartidas o dll con código compilado (normalmente escrito en C) que tienen funciones (manejo de memoria, erroes, abases de datos..)
utilizadas por diferentes programas a la vez para reducir su tamaño simplificar su mantenimiento y reducir el consumo de memoria del sistema, 
tambien pueden interactuar con el hardware (por ejemplo para controladores de dispositivos) 

Cuando una aplicación necesita utilizar una función que se encuentra en una DLL, se carga la biblioteca en memoria y se vincula dinámicamente con 
el programa. 
- Las de Windows tienen la extension ".dll" . Estan en "System32" o "SysWOW64".  
- Las de linux tienen la extension ".so". Se almacenan en  "/usr/lib" o "/lib".  

### Drivers
Los drivers permiten que SO y los programas puedan interactuar con dispositivos de hardware específicos (ej tarjeta de sonido). Por lo que cada
uno tiene los suyos propios. Se cargan en memoria durante el arranque del sistema operativo y se vinculan dinámicamente con el kernel.







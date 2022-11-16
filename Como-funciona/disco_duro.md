

## Tipos de disco duro

HDD -> **hard disk** -> un disco que gira y una aguja magnetica que va escribiendo la informacion en él. Esta dividido en trozitos (pistas magneticas) y la aguja
imanta cada uno dandole un valor magnetico positivo o negativo que equivale a 0 o 1. Es todo mas *analógico*. Suele haber varios discos/agujas  
(como un sandwich, alternandose encima unos de otros). Es mas lento que el SDD y resiste peor los golpes.

SDD -> **solid state** -> almacena la informacion de manera electronica (en base a puertas logicas que almacenan un estado "0" u otro "1" ). No necesita energia para
almacenar los datos adiferencia de la volatil memoria RAM. Los pendrives funcionan de esta manera.

Fuentes: \[ [1](https://youtu.be/xBzeiZzYELw), [2](https://youtu.be/fTRxLMJn_Jg) ]

----------------------------------------

## Sistema de archivos. Particiones

El sistema de archivos hace que ordenador almacene datos (archivos, a ser posible ordenados), aaceda a ellos, los borre, mueva, los recupere y administre quien
acceda a ellos (permisos o ACLs).

Un disco duro se puede dividir en particiones.

1. **FAT32** -> sistema obsoleto (no permite archivos mayores que 4gb ni particiones masyores de 8tb). Evoluciono a **EXFAT** 
 
2. **NTFS** -> Es el que utiliza Windows por defecto. (archivos de hasta 16tb). Transaccional y permite cifrado.
Transaccional: los archivos tienen metadatos (informacion como por ejemplo lo que ocupa, la ruta donde esta almacenado, el usaurio propietario...) Tambien tiene un
"diario" que los cambios que se estan realizando en el disco (por ejemplo copiar un archivo) y si se cuelga el sistema de golpe, gracias al diario, cuando se reinicie,
podra continuar y acabar esa tarea pendiente.

3. **EXT4** ->  Sistema utilizado por Linux (el equivalente en caracteristicas al ntfs de windows). Tambien es transaccional y permite archivos de gran tamaño.

Fuentes -> [GioCode](https://www.youtube.com/c/giova50000), [redeszone](https://www.redeszone.net/tutoriales/servidores/sistemas-archivos-ext4-btfs-zfs-elegir/)

----------------------------------------

## Fragmentacion de un disco

Un disco duro almacena los datos, pero no lo hace de manera ordenada (o sea no dejando espacio vacio entre donde acaba archivo y empieza el siguiente) sino que escribe
donde primero le pilla.  
Que esté guardado de manera tan random hace que al acceder a un archivo le cueste mas trabajo (ya que esta muy desordenado y pierde tiempo 
leyendo muchos espacios vacios ). Asi que si queremos ordenar, le tenemos que decir que mueva un archivo detras de otro y que deje todo el espacio sin usar al final
(**desfragmentar**).
```
Desfragmentado -> [Sistema Operativo] [Peliculas] [ Microsoft Office ] [ Documentos ] [ Minecraft ]  [  Vacio                            ] 
Fragmentado    -> [Sistema Operativo] [ Vacio ] [ Peliculas ] [ Vacio ] [ Microsoft Office ] [ Documentos ] [      Vacio  ]  [ Minecraft ]
```










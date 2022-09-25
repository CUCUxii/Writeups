¡DISCLAIMER! Al ser estudiante y no disponer de todos los conocimientos he ido haciendo los retos gracias a writeups como los de Jhon Hammond. Una vez
resuleto y entendido, traslado los concimientos adquiridos aqui.

## FIletypes

Nos dan un pdf y al abrirlo con vim vemos que es un shell_archive (similar a un script en bash). El codigo es muy lioso, pero las lineas comentadas de
arriba nos dicen que lo ejecutemos con ```sh File.pdf``` Antes de hacerlo vi que no hubiera ningun codigo malicioso como *rm* y demas.
```~:$ sh Flag.pdf # -> Flag.pdf: 119: uudecode: not found```

Nos dicen que uudecode no se encuentra, lo mire en el codigo y le pasa a ese comando un texto encriptado. Ese comando tiene una descripcion en wikipedia.
> UUEncode proviene de UNIX to Unix Encoding. Se trata de un algoritmo de codificación que transforma código binario en texto.
Lo instale con `sudo apt-get install sharutils` y corri el script de nuevo, ya no dio errores y creo un archivo "flag". 

Como consejo cuando sabes de que es un archivo, esta bien renombrarlo con su extension correspondiente.  

**ar** -> El sistema creo un archivo *ar*. Leyendo de wikipedia dice que es un formato de archivo comprimido y que fue sustituido por tar (como un zip)
Hice ```ar flag.ar``` y me dio error por faltar parametros, di con que *x* es para descomprimir (y *v* verbose). ``` ar xv flag.ar```  
**cpio** ->  nuevo archivo, un "cpio" (otro zip raro). Lo renombro a ```flag.cpio``` asi que *--help* y luego ```cpio --file ./flag.cpio --extract```.
**bzip2** -> Otro nuevo ```bzip2 --decompress ./flag.bzip2 -v```, El resto, **gzip** lo extraje con ```7z x``` (descromprime casi todo tipo
de archivos). LUego vino **lzip**,**lzma**,**lzop** y un par mas. Al decimo archivo o por ahi tenemos la flag (estaba en hexadecimal.)

------------------------------------------------

## Lookey here

Nos dan un archivo de texto y nos dicen que se ha escondido informacion en el. **wc -l** nos dice que tiene mas de 2000 lineas. COn grep ha sido una
chorrada. -> ```~:$ cat anthem-flag.txt | grep -oEn "picoCTF{.*?}" # -> (linea 933) -> picoCTF{gr3p_15_@w3s0m3_58f5c024}```

------------------------------------------------

## Enhance!

Nos dan una foto, si la abro sale com un circulo negro enorme con unos pequeños numeros. La flag tiene que estar en los metadatos, pero **exiftool**
no me dice nada relevante mas que a parte de una foto es un **xml**. Una imagen es un archivo binario y si le haces cat te saldran caracteres ilegibles
(el ascii de los bytes en hexadecimal), pero con este me sale un *xml* normal. COn **grep** busque la plaabra *pico* y no la encontre pero si un *}*.
Abri el archivo con vim y encontre el resto de letras de la flag solo que separadas y entre lienas al lado de un patron "id=tspan". 
```console
~$: cat drawing.xml | grep -oE 'id="tspan.*?">.*?' | awk '{print $2}' FS=">" | sed 's/<\/tspan//g' | xargs | tr -d " "
picoCTF{3nh4nc3d_24374675}
```
> Esta todo/xml no era una foto hecha a partir de plasmarla en mapa de bits (o sea normal) sino a partir de unas instrucciones en xml de como crearla

------------------------------------------------

## Packets Primer

Tenemos un archivo pcap. Estos archivos son la captura de una transmision de datos entre ordenadores (o sea conexiones grabadas). Se abre con wireshark.
```wireshark picoctf_captura.cap >/dev/null 2>&1 &; disown```
Ahi nos encontramos varios paquetes (5). Ignoramos los tres primeros (\[SYN], \[SYN ACK], \[ACK]) porque no son mas que los dos ordenadores diciendo que 
la conexion se ha podido establecer correctamnte por tcp. El quinto es para ver que la data se ha recibido correctamente. Nos interesa el 4º que son los
datos en si (\[PSH-ACK]). En la seccion de "Data", nos sale el mensaje ne hexadecimal y ascii. "Ctrol Shif+o" y vemos el mensaje, la flag.
*picoCTF{p4ck37_5h4rk_b9d53765}*

------------------------------------------------

## Redaction gone wrong

Nos dan un pdf, lo he abierto con el navegador y el wrapper *file:\///rutaabolsuta* y sale un docoumento de un par de frases y unas cuantas tachadas en 
negro (no se ven), estas he seleccionado el texto que dentro habia, lo he copiado y sale esto. 
*"Breakdown  This is not the flag, keep looking picoCTF{C4n_Y0u_S33_m3_fully"* Le añadi un "}" más. Aun asi hay una utilidad llamada **pdftotext**
que te puede extraer todo el texto, ya que si abres un pdf como un editor de texto te encontraras un formato ilegible.

------------------------------------------------

## Eavesdrop

Nos dan otra vez una captura.pcap y hay que analizarla con el wireshark. ESta vez es una larga conversacion entre dos equipos de una misma red
(10.0.2.4 y 10.0.2.15),  pongo *tcp* en el filtrador para eliminar ruido y le doy ctrol+dcho "seguir -> flujo TCP"  
Es una conversacion entre dos personas donde se han pasado un paquete por el puerto 9002 (puede que usando netcat) y con este comando
```openssl des3 -d -salt -in file.des3 -out file.txt -k supersecretpassword123```
Si filtramos por ese puerto ("tcp.port eq 9002" en filtro) En el paquete \[PSH-ACK] tenemos la data "Salted__}..O.G....^..GZ	LbvbJ5eYm...R...,@.M.U.."
hay que mostrarlo en formato Raw (o sea los bytes sin conversion ascii) y exportarlo (save as) con el nombre file.de. Aplicas el comando de arriba 
sobre el archivo y tienes la flag. 

Si no quieres usar wireshark, la herramienta ```tcpflow -r captura.pcap``` te hace todos estos pasos mas rapidamente.

------------------------------------------------

## Torrent Analyze

Nos dan otra captura.pcap Se supone que alguien ha bajado documentos por torrent. Abrimos la captura con wireshark y damos con muchos paquetes de datos
UDP (por tanto el tcpflow aqui no nos puede ayudar mucho). En hints nos dicen de activar en "Analyze -> Enabled Protocols" bit torrent BT-DHT.
















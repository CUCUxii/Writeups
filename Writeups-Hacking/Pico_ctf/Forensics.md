¡DISCLAIMER! Al ser estudiante y no disponer de todos los conocimientos he ido haciendo los retos gracias a writeups como los de Jhon Hammond. Una vez
resuleto y entendido, traslado los concimientos adquiridos aqui.

## FIletypes

Nos dan un pdf y al abrirlo con vim vemos que es un shell_archive (similar a un script en bash). El codigo es muy lioso, pero las lineas comentadas de
arriba nos dicen que lo ejecutemos con ```sh File.pdf``` Antes de hacerlo vi que no hubiera ningun codigo malicioso como *rm* y demas.
```console
~:$ sh Flag.pdf
x - created lock directory _sh00046.
x - extracting flag (text)
Flag.pdf: 119: uudecode: not found
```
Nos dicen que uudecode no se encuentra, lo mire en el codigo y le pasa a ese comando un texto encriptado. Ese comando tiene una descripcion en wikipedia.
> UUEncode proviene de UNIX to Unix Encoding. Se trata de un algoritmo de codificación que transforma código binario en texto.
Lo instale con ```sudo apt-get install sharutils```y corri el script de nuevo, ya no dio errores y creo un archivo "flag". 

Como consejo cuando sabes de que es un archivo, esta bien renombrarlo con su extension correspondiente.  

**ar** -> El sistema creo un archivo *ar*. Leyendo de wikipedia dice que es un formato de archivo comprimido y que fue sustituido por tar (como un zip)
Hice ```ar flag.ar``` y me dio error por faltar parametros, di con que *x* es para descomprimir (y *v* verbose). ``` ar xv flag.ar```  
**cpio** ->  nuevo archivo, un "cpio" (otro zip raro). Lo renombro a ```flag.cpio``` asi que *--help* y luego ```cpio --file ./flag.cpio --extract```.


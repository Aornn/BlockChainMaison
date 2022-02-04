from urllib import response
from flask import Flask, request, jsonify
import requests,json,hashlib,time,multiprocessing

app = Flask(__name__)
difficulty = 4
hard_nodes = {}
f = None
# https://bitcoin.stackexchange.com/questions/38190/where-can-i-find-a-list-of-reliable-bitcoin-full-nodes
ip_host = "127.0.0.1:5000"

# Ajout de l'ip de notre validator à tous les noeuds renseignés dans le fichier json.
def add_validator_to_bc():
    global hard_nodes,f
    f = open('nodes_main.json','r+')
    hard_nodes = json.load(f)
    hard_nodes['length_nodes_ip'] = len(hard_nodes['nodes_ip'])
    print(hard_nodes)
    payload = {
        "host" : ip_host
    }
    for ip in hard_nodes['nodes_ip']:
        try :
            r = requests.post("http://"+ip+"/validator", json=payload)
            print(r.text)
        except:
            continue

# Calcul du hash du block donné en parametre.
def calculate_hash(data):
    nonce = 0
    obj = {"prev" : data['prev'], "timestamp" : data['timestamp'], "data" : data['data'] ,"nonce" : nonce}
    h = hashlib.sha256(json.dumps(obj).encode("utf-8")).hexdigest()
    start = time.time()
    while h.startswith("0"*difficulty) == False:
        obj['nonce'] = nonce
        h = hashlib.sha256(json.dumps(obj).encode("utf-8")).hexdigest()
        nonce += 1
    end = time.time()
    obj['time_elapsed'] = end - start
    obj['hash'] = h
    print("bloc envoyé : ", obj)
    for ip in hard_nodes['nodes_ip']:
        try :
            r = requests.post("http://"+ip+"/addblock", json=obj)
            print(r.text)
        except:
            continue

# Vérifie si le block est en vie.
@app.route('/isalive', methods=['GET'])
def is_alive():
    response = {
        'message' : 'ALIVE',
    }
    return jsonify(response), 200

# Route appelé lorsque qu'il y a besoin de valider/ajouter un block.
# Si la requete vient d'un noeud inconnue, nous l'ajoutons à notre list de noeuds connus.
@app.route('/validation', methods=['POST'])
def validation():
    global hard_nodes,f
    data = request.get_json()
    from_ip = request.args.get('from_ip')
    if from_ip not in hard_nodes['nodes_ip']:
        hard_nodes['nodes_ip'].append(from_ip)
        hard_nodes['length_nodes_ip'] = len(hard_nodes['nodes_ip'])
        f.seek(0)
        json.dump(hard_nodes, f)
        f.truncate()
    calculate = multiprocessing.Process(target=calculate_hash,args=[data])
    calculate.start()
    response = {
        'message' : 'Data received'
    }
    return jsonify(response), 200

if __name__ == "__main__":
    add_validator_to_bc()
    app.run(host='127.0.0.1', port=5000)
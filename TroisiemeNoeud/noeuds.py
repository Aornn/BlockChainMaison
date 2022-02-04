import settings
from flask import Flask, request, jsonify
from utils_fnc import save_hardnodes, add_validator_to_bc,verif, update_validator_nodes, synchronise_run, add_nodes_to_bc
import json,requests,time,multiprocessing
app = Flask(__name__)

# Node


# Cette endpoint nous sert pour ajouter un noeuds dans notre liste de noeuds connus.
# Si le noeuds nest pas dans notre liste, nous l'ajoutons et nous sauvegardons cette liste dans un fichier json.
# Puis nous renvoyons au demmandeur notre liste de noeuds connus.
@app.route('/node', methods=['POST'])
def post_node():
    data = request.get_json()
    if data['ip_to_add'] not in settings.hard_nodes["nodes_ip"] and data['ip_to_add'] != settings.node_ip:
        settings.hard_nodes["nodes_ip"].append(data['ip_to_add'])
        settings.hard_nodes['length_nodes_ip'] = len(settings.hard_nodes["nodes_ip"])
        save_hardnodes(settings.hard_nodes,settings.node_ip)
        nodes_to_send = settings.hard_nodes["nodes_ip"].copy()
        nodes_to_send.remove(data['ip_to_add'])
        nodes_to_send.append(settings.node_ip)
        response = {
            'message' : 'OK',
            'node_added' : data['ip_to_add'],
            'validator' : settings.hard_nodes["validator_ip"],
            'len_validator' : settings.hard_nodes["length_validator_ip"],
            'len_nodes' : settings.hard_nodes["length_nodes_ip"],
            'nodes' : nodes_to_send
        }
        return jsonify(response), 201
    else:
        response = {
            'message' : 'OK',
            'node_added' : 'already present',
            'validator' : settings.hard_nodes["validator_ip"],
            'len_validator' : settings.hard_nodes["length_validator_ip"],
            'len_nodes' : settings.hard_nodes["length_nodes_ip"],
            'nodes' : settings.hard_nodes["nodes_ip"]
        }
        return jsonify(response), 200

# Retourne toutes les informations du noeuds.
# Node, validator etc ...
@app.route('/node', methods=['GET'])
def config():
    response = {
        'message' : 'OK',
        'config' : settings.hard_nodes
    }
    return jsonify(response), 200

# Permet de réinitialiser la liste des validator par les validator passez en body.
# Il n'y a aucune vérification, on pourrait parcourir toute la liste des validator recu et ajouter uniquement ceux
# que nous n'avons pas. En meme temps, il faudrait que nous retirions tous nos validator qui ne répondent plus.
@app.route('/resetvalidator', methods=['POST'])
def reset_validator():
    data = request.get_json()
    if len(data) < settings.hard_nodes['validator_ip']:
        response = {
        'message' : 'KO',
        'description' : 'Pas besoin de maj'
        }
        return jsonify(response), 200
    settings.hard_nodes['validator_ip'] = data
    settings.hard_nodes['length_validator_ip'] = len(settings.hard_nodes['validator_ip'])
    save_hardnodes(settings.hard_nodes,settings.node_ip)
    response = {
        'message' : 'OK',
        'total_validator' : len(settings.hard_nodes['validator_ip'])
    }
    return jsonify(response), 201

# Ajout d'un validator dans notre liste de validator. Le nouveau validator sera stocké et notre fichier json sera mis à jour.
@app.route('/validator', methods=['POST'])
def add_validator():
    data = request.get_json()
    total = add_validator_to_bc(data["host"], settings.node_ip)
    response = {
        'message' : 'OK',
        'total_validator' : total
    }
    return jsonify(response), 201

# Ajout d'un block à notre blockchain. L'ajout ne se fera unqiuement que si le block que l'on veut ajouter est différent du dernier bloc actuelle
# et que si le hash du bloc n-1 correspond au hash du bloc précédent renseigné dans le bloc actuelle (fonciton verif).
# Si tout est bon, on transmet le nouveau bloc à tous les noeuds connus qui ont feront de même.
@app.route('/addblock', methods=['POST'])
def add_block():
    block = request.get_json()
    from_ip = request.args.get('from_ip')
    b = open('blockchain.json', 'r+')
    blockchain = json.load(b)
    if block['hash'] == blockchain["block"][blockchain['length']-1]['hash']:
        response = {
            'message' : 'OK',
            'block_added' : "BLOCK already present"
        }
        return jsonify(response), 200
    if verif(block):
        blockchain["length"] = int(blockchain["length"]) + 1
        blockchain["block"].append(block)
        blockchain["lasthash"] = block['hash']
        b.seek(0)  # rewind
        json.dump(blockchain, b)
        b.truncate()
        for c_node_ip in settings.hard_nodes["nodes_ip"]:
            if c_node_ip != settings.node_ip and c_node_ip != from_ip:
                try:
                    r = requests.post("http://"+c_node_ip+"/addblock?from_ip="+settings.node_ip, json=block)
                except:
                    continue
        response = {
            'message' : 'OK',
            'block_added' : block
        }
        return jsonify(response), 201
    else:
        response = {
            'message' : 'KO',
            'block_added' : "wrong block"
        }
        return jsonify(response), 400

# Retounr la longeur de notre blockain stocké sur ce neuds. Utile pour pouvoir comparer quelle blockchain est la plus grande.
# On considère que la blockchain la plus grande sera la bonne. Bien sur c'est sommaire mais ca nous conviendra.
@app.route('/lengthblockchain', methods=['GET'])
def length_blockchain():
    b = open('blockchain.json', 'r')
    blockchain = json.load(b)
    response = {
        'message' : 'OK',
        'length' : blockchain['length']
    }
    return jsonify(response), 200

# Meme logique que l'endpoint resetvalidator. Attention tout de meme pour des raisons de facilité, ici il n'y a aucune vérification de la données recus.
# Ce qui veut dire que n'importe qui pourrait envoyer n'importe quoi et faire planter notre noeud.
# Dans l'idéal, il faudrait vérifier les données recus. On pourrait vérifier toute la blockchain recu grace au nonce.
# Une fois fait on partagerai la blockchain avec les autres noeuds et si minimum 51% des noeuds sont ok avec la blockchain recu on l'ajoute.
# Donc cette opération pourrait demander beaucoup de temps mais un reset de blockchain n'est pas à prendre à la légère...
@app.route('/resetblockchain', methods=['POST'])
def reset_blockchain():
    blockchain_receive = request.get_json()
    b = open('blockchain.json', 'r+')
    b.seek(0)  # rewind
    json.dump(blockchain_receive, b)
    b.truncate()
    response = {
        'message' : 'OK',
        'block_added' : blockchain_receive
    }
    return jsonify(response), 201

# Retourne la blockchain stocké sur le noeud.
@app.route('/getblockchain', methods=['GET'])
def get_blockchain():
    b = open('blockchain.json', 'r+')
    blockchain = json.load(b)
    response = {
        'message' : 'OK',
        'blockchain' : blockchain
    }
    return jsonify(response), 200


# Force la synchronisation du noeud par rapport aux autres noeuds.
# La fonction update_validator_nodes va permettre de mettre à jour les validateurs
# Et synchronise_run, de mettre à jour la blockchain si besoin par rapport aux autre noeuds
# On pourrait imaginer de mettre à jour le noeuds non plus par endpoint mais par tache d'arrière plan.
# Par exemple toutes les n heures, on éxécuterai la tache pour vérifier l'intégrité du noeud.
@app.route('/synchronize', methods=['GET'])
def synchronise():
    b = open('blockchain.json', 'r')
    blockchain = json.load(b)
    update_validator_run = multiprocessing.Process(target=update_validator_nodes, args=[settings.node_ip])
    synchro = multiprocessing.Process(target=synchronise_run,args=[blockchain,settings.node_ip])
    synchro.start()
    update_validator_run.start()
    response = {
        'message' : 'OK',
        'synchronise' : 'IN PROGRESS'
    }
    return jsonify(response), 200


# Cet endoint recupere les datas dans le body et va l'envoyer à tous ses validateurs pour demander un calcul.
@app.route('/sendblock', methods=['POST'])
def send_block():
    data = request.get_json()
    if data['Name'] == "" or data['From'] == "" or data['To'] == "":
        response = {
        'message' : 'KO',
        'description' : "bad block"
        }
        return jsonify(response), 200
    b = open('blockchain.json', 'r+')
    blockchain = json.load(b)
    payload = {
        "prev" : blockchain["block"][len(blockchain["block"])-1]["hash"],
        "timestamp" : time.time(),
        "from" : settings.node_ip,
        "data" : {
            "Name" : data['Name'],
            "From" : data['From'],
            "To" : data['To']
        }
    }
    for validator in settings.hard_nodes['validator_ip']:
        try:
            r = requests.post("http://"+validator+"/validation?from_ip="+settings.node_ip, json=payload)
            print(r.text)
        except:
            continue
    response = {
        'message' : 'OK',
        'send_to' : settings.hard_nodes
    }
    return jsonify(response), 200

if __name__ == "__main__":
    # Cette fonction va etre éxécuté à chaque fois qu'un noeuds est lancé, elle permet de mettre à jour ses validateurs et les autres noeuds du réseau.
    add_nodes_to_bc(settings.node_ip)
    print(settings.hard_nodes)
    app.run(host='127.0.0.1', port=5003)
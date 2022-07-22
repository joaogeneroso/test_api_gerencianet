import re
from urllib import response
from app import app
from .. import request, render_template
from gerencianet import Gerencianet
from app.credentials import CREDENTIALS


gn = Gerencianet(CREDENTIALS)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/information_banking_billet/')
def banking_billet():
    return render_template('banking_billet.html')


@app.route('/information_credit_card/')
def information_credit_card():
    return render_template('credit_card.html')


@app.route('/information_carnet/')
def information_carnet():
    return render_template('carnet.html')

@app.route('/info/')
def info():
    return render_template('info.html')

@app.route('/information_plan/')
def information_plan():
    return render_template('plan.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')


@app.route('/create_banking_billet/', methods=['POST'])
def create_banking_billet():
    body = {
        'items': [{
            'name': request.form['descricao'],
            'value': int(request.form['valor'].replace(',', '').replace('.', '')),
            'amount': int(request.form['quantidade'])
        }],
        'payment': {
            'banking_billet': {
                'expire_at': request.form['vencimento'],
                'customer': {
                    'name': request.form['nome_cliente'],
                    'phone_number': request.form['telefone'].replace(' ', '').replace('-', ''),
                    'cpf': request.form['cpf'].replace('.', '').replace('-', '')
                }
            }
        }
    }

    response = gn.create_charge_onestep(params=None, body=body)

    if response['code'] == 200:

        phone_number = request.form['telefone'].replace(' ', '').replace('-', '')
        value = request.form['valor']
        description = request.form['descricao']
        expire_at = request.form['vencimento']
        link_download = response['data']['pdf']['charge']
        barcode = response['data']['barcode']

        shareLink = 'https://api.whatsapp.com/send'
        shareLink += f'?phone=55{format_phone_number(phone_number)}+&'
        shareLink += f'text=Olá, segue o boleto no valor de R$ {value}. '
        shareLink += f'Cobrança referente à {description}, '
        shareLink += f'com vencimento para {expire_at}. '
        shareLink += f'Acesse o boleto pelo link: {link_download}'
        shareLink += f' ou pague usando o código de barras: {barcode}.'
        return render_template('conf_banking_billet.html', link_down=link_download, shareLink=shareLink, copy=barcode)
    else:
        return render_template('error.html')


@app.route('/create_credit_card/', methods=['POST'])
def create_credit_card():
    body = {
        'items': [{
            'name': request.form['descricao'],
            'value': int(request.form['valor']),
            'amount': int(request.form['quantidade'])
        }],
        'payment': {
            'credit_card': {
                'installments': int(request.form['installments']),
                'payment_token': request.form['payament_token'],
                'billing_address': {
                    'street': request.form['rua'],
                    'number': request.form['numero'],
                    'neighborhood': request.form['bairro'],
                    'zipcode': str(request.form['cep']),
                    'city': request.form['cidade'],
                    'state': request.form['estado']
                },
                'customer': {
                    'name': request.form['nome_cliente'],
                    'email': request.form['email'],
                    'cpf': request.form['cpf'],
                    'birth': request.form['nascimento'],
                    'phone_number': request.form['telefone'].replace(" ", "").replace("-", "")
                }
            }
        }
    }

    response = gn.create_charge_onestep(params=None, body=body)

    if response['code'] == 200:
        charge_id = str(response['data']['charge_id'])
        return render_template('conf_credit_card.html', copy=charge_id)
    else:
        return render_template('error.html')


@app.route('/create_carnet/', methods=['POST'])
def create_carnet():
    body = {
        'items': [{
            'name': request.form['descricao'],
            'value': int(request.form['valor'].replace(',', '').replace('.', '')),
            'amount': int(request.form['quantidade'])
        }],
        'customer': {
            'name': request.form['nome_cliente'],
            'email': request.form['email'],
            'cpf': request.form['cpf'].replace(".", "").replace("-", ""),
            'phone_number': request.form['telefone'].replace(" ", "").replace("-", "")
        },
        'repeats': int(request.form['parcelas']),
        'expire_at': request.form['vencimento']
    }

    if len(request.form['instrucao']) > 0:
        body.update({'message': request.form['instrucao']})

    response = gn.create_carnet(body=body)

    if response['code'] == 200:
        carnet_link = response['data']['pdf']['carnet']
        carnet_id = response['data']['carnet_id']
        charges = response['data']['charges']
        return render_template('conf_carnet.html', carnet_id=carnet_id, carnet_link=carnet_link, charges=charges)
    else:
        return render_template('error.html')

@app.route('/create_info/', methods=['POST'])
def conf_inf():
    params = {
    'id': request.form['id']
    }

    response =  gn.detail_charge(params=params)

    if response['code'] == 200:
        status = str(response['data']['status'])
        name = str(response['data']['items'][0]['name'])

        return render_template('conf_info.html', status=status, name=name)
    else:
        return render_template('error.html')

@app.route('/create_plan/', methods=['POST'])
def create_plan():
    body = {
        'items': {
            'name': str(request.form['name']),
            'interval': int(request.form['periodicidade']),
            'repeats': int(request.form['parcelas'])           
        }
    }

    response =  gn.create_plan(body=body)

    if response['code'] == 200:
        return render_template('conf_info.html')
    else:
        return render_template('error.html')


def format_phone_number(str_phone, i=2):
    return str_phone[:i] + str_phone[i+1:]

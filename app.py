from flask import Flask, render_template
from flask.ext.wtf import Form
from wtforms import RadioField
from datetime import datetime
import config
import pydocumentdb.document_client as document_client

app = Flask(__name__)
app.config.from_object('config')


class VoteForm(Form):
    deploy_preference = RadioField('Deployment Preference', choices=[
        ('Web Site', 'Web Site'),
        ('Cloud Service', 'Cloud Service'),
        ('Virtual Machine', 'Virtual Machine')], default='Web Site')


@app.route('/create')
def create():
    """Renders the contact page."""
    client = document_client.DocumentClient(config.DOCUMENTDB_HOST, {'masterKey': config.DOCUMENTDB_KEY})

    # Attempt to delete the database.  This allows this to be used to recreate as well as create
    try:
        db = next((data for data in client.ReadDatabases() if data['id'] == config.DOCUMENTDB_DATABASE))
        client.DeleteDatabase(db['_self'])
    except:
        pass

    # Create database
    db = client.CreateDatabase({'id': config.DOCUMENTDB_DATABASE})

    # Create collection
    collection = client.CreateCollection(db['_self'], {'id': config.DOCUMENTDB_COLLECTION})

    # Create document
    document = client.CreateDocument(collection['_self'],
                                     {'id': config.DOCUMENTDB_DOCUMENT,
                                      'Web Site': 0,
                                      'Cloud Service': 0,
                                      'Virtual Machine': 0,
                                      'name': config.DOCUMENTDB_DOCUMENT
                                      })

    return render_template(
        'create.html',
        title='Create Page',
        year=datetime.now().year,
        message='You just created a new database, collection, and document.  Your old votes have been deleted')


@app.route('/vote', methods=['GET', 'POST'])
def vote():
    form = VoteForm()
    replaced_document = {}
    if form.validate_on_submit():  # is user submitted vote
        client = document_client.DocumentClient(config.DOCUMENTDB_HOST, {'masterKey': config.DOCUMENTDB_KEY})

        # Read databases and take first since id should not be duplicated.
        db = next((data for data in client.ReadDatabases() if data['id'] == config.DOCUMENTDB_DATABASE))

        # Read collections and take first since id should not be duplicated.
        coll = next(
            (coll for coll in client.ReadCollections(db['_self']) if coll['id'] == config.DOCUMENTDB_COLLECTION))

        # Read documents and take first since id should not be duplicated.
        doc = next((doc for doc in client.ReadDocuments(coll['_self']) if doc['id'] == config.DOCUMENTDB_DOCUMENT))

        # Take the data from the deploy_preference and increment our database
        doc[form.deploy_preference.data] = doc[form.deploy_preference.data] + 1
        replaced_document = client.ReplaceDocument(doc['_self'], doc)

        # Create a model to pass to results.html
        class VoteObject:
            choices = dict()
            total_votes = 0

        vote_object = VoteObject()
        vote_object.choices = {
            "Web Site": doc['Web Site'],
            "Cloud Service": doc['Cloud Service'],
            "Virtual Machine": doc['Virtual Machine']
        }
        vote_object.total_votes = sum(vote_object.choices.values())

        return render_template(
            'results.html',
            year=datetime.now().year,
            vote_object=vote_object)

    else:
        return render_template(
            'vote.html',
            title='Vote',
            year=datetime.now().year,
            form=form)


if __name__ == '__main__':
    app.run()

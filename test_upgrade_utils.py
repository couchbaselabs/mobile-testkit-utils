import pytest
import time
import pickle

from CBLClient.Document import Document
from CBLClient.Replication import Replication
from keywords.MobileRestClient import MobileRestClient
from libraries.testkit import cluster
from boto.dynamodb import batch
from CBLClient.Database import Database


@pytest.mark.listener
@pytest.mark.replication
def test_db_preperation(params_from_base_test_setup):
    """
    @summary:
    1. Create docs in CBL and replicate to SG using push one-shot replication
    2. start push one-shot replication and start replication event listener
    3. Check the error is thrown in replication event changes as CBS can't have doc greater than 20mb
    """
    sg_db = "db"
    sg_admin_url = params_from_base_test_setup["sg_admin_url"]
    cluster_config = params_from_base_test_setup["cluster_config"]
    sg_blip_url = params_from_base_test_setup["target_url"]
    base_url = params_from_base_test_setup["base_url"]
    sg_config = params_from_base_test_setup["sg_config"]
    db = params_from_base_test_setup["db"]
    cbl_db = params_from_base_test_setup["source_db"]
    sync_gateway_version = params_from_base_test_setup["sync_gateway_version"]
    liteserv_platform = params_from_base_test_setup["liteserv_platform"]
    liteserv_version = params_from_base_test_setup["liteserv_version"]
    cbl_db_name = "travel-sample"

    # 1. Creating Docs in CBL
    db_name = db.getName(cbl_db)
    db.deleteDB(cbl_db, db_name)
    cbl_db_name = "copiedDB" + str(time.time())
    new_db_name = "travel-sample_{}".format(liteserv_version)
    new_cbl_db = db.create(new_db_name)
    print db.getPath(new_cbl_db)
    print db.getCount(database=new_cbl_db)
    db_config = db.configure()
    if liteserv_platform == "android":
        prebuilt_db_path = "/assets/PrebuiltDB.cblite2.zip"
    elif liteserv_platform == "xamarin-android":
        prebuilt_db_path = "PrebuiltDB.cblite2.zip"
    else:
        prebuilt_db_path = "Databases/travel-sample.cblite2"

    db.copyDatabase(prebuilt_db_path, cbl_db_name, db_config)
    cbl_db = db.create(cbl_db_name, db_config)

    doc_ids =  db.getDocIds(database=cbl_db, limit=40000)


    docs_data = db.getDocuments(database=cbl_db, ids=doc_ids)
    with open("doc_data.pkl", "wb") as fh:
        pickle.dump(docs_data, fh, pickle.HIGHEST_PROTOCOL)
    print "done"
#     db.saveDocuments(database=new_cbl_db, documents=docs_data)
#     print db.getCount(database=new_cbl_db)


def test_write_data_to_db(params_from_base_suite_setup):
    base_url = params_from_base_suite_setup["base_url"]
    db = Database(base_url)
    liteserv_version = params_from_base_suite_setup["liteserv_version"].split("-")[0]
    encrypted_db_name = "travel-sample-encrypted-{}".format(liteserv_version)
    unencrypted_db_name = "travel-sample-{}".format(liteserv_version)
    encrypted_db_config = db.configure(password="password")
    unencrypted_db_config = db.configure()
    cbl_db_1 = db.create(encrypted_db_name, config=encrypted_db_config)
    cbl_db_2 = db.create(unencrypted_db_name, config=unencrypted_db_config)
    print db.getPath(cbl_db_1)
    print db.getPath(cbl_db_2)
    fh = open("doc_data.pkl", "rb")
    docs_data = pickle.load(fh)
    doc_count = len(docs_data)
    start = 0
    batch_size = 1000
    keys = docs_data.keys()
    keys.sort()
    while(doc_count>0):
        end = start+batch_size
        if end > 31591:
            end = 31591
        process_keys = keys[start:end]
        docs = {doc_id: docs_data[doc_id] for doc_id in process_keys}
        db.saveDocuments(cbl_db_1, docs)
        db.saveDocuments(cbl_db_2, docs)
        print "{}:{}".format(start, end)
        start += batch_size
        doc_count -= batch_size
    print db.getCount(database=cbl_db_1)
    print db.getCount(database=cbl_db_2)
    ts_db_path1 = db.getPath(cbl_db_1)
    ts_db_path2 = db.getPath(cbl_db_2)
    print ts_db_path1
    print ts_db_path2
    print "done"

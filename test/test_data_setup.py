"""Script to test data generation functions."""
from __future__ import print_function
from __future__ import absolute_import

import os
import numpy as np
from random import random

from ase.ga.data import DataConnection

from atoml import __path__ as atoml_path
from atoml.api.ase_data_setup import get_unique, get_train
from atoml.fingerprint import FeatureGenerator
from atoml.fingerprint.neighbor_matrix import neighbor_features
from atoml.fingerprint.periodic_table_data import (get_mendeleev_params,
                                                   default_params)
from atoml.cross_validation import k_fold
from atoml.utilities import DescriptorDatabase

atoml_path = '/'.join(atoml_path[0].split('/')[:-1])
wkdir = os.getcwd()

# Perform expensive feature generation on small test set only.
train_size, test_size = 50, 3


def feature_test():
    """Generate features from atoms objects."""
    # Test generic features for Pt then both Pt and Au.
    get_mendeleev_params(atomic_number=78)
    get_mendeleev_params(atomic_number=[78, 79],
                         params=default_params + ['en_ghosh'])

    # Connect database generated by a GA search.
    gadb = DataConnection('{}/data/gadb.db'.format(atoml_path))

    # Get all relaxed candidates from the db file.
    print('Getting candidates from the database')
    all_cand = gadb.get_all_relaxed_candidates(use_extinct=False)

    # Setup the test and training datasets.
    testset = get_unique(atoms=all_cand, size=test_size, key='raw_score')
    assert len(testset['atoms']) == test_size
    assert len(testset['taken']) == test_size

    trainset = get_train(atoms=all_cand, size=train_size,
                         taken=testset['taken'], key='raw_score')
    assert len(trainset['atoms']) == train_size
    assert len(trainset['target']) == train_size

    # Clear out some old saved data.
    for i in trainset['atoms']:
        del i.info['data']['nnmat']

    # Initiate the fingerprint generators with relevant input variables.
    print('Getting the fingerprints')
    f = FeatureGenerator(element_parameters='atomic_radius')
    f.normalize_features(trainset['atoms'], testset['atoms'])

    data = f.return_vec(trainset['atoms'], [f.nearestneighbour_vec])
    n, d = np.shape(data)
    assert n == train_size and d == 4
    print('passed nearestneighbour_vec')

    train_fp = f.return_vec(trainset['atoms'], [f.bond_count_vec])
    n, d = np.shape(train_fp)
    data = np.concatenate((data, train_fp), axis=1)
    assert n == train_size and d == 52
    print('passed bond_count_vec')

    train_fp = f.return_vec(trainset['atoms'], [f.distribution_vec])
    n, d = np.shape(train_fp)
    data = np.concatenate((data, train_fp), axis=1)
    assert n == train_size and d == 8
    print('passed distribution_vec')

    # EXPENSIVE to calculate. Not included in training data.
    train_fp = f.return_vec(testset['atoms'], [f.connections_vec])
    n, d = np.shape(train_fp)
    assert n == test_size and d == 26
    print('passed connections_vec')

    train_fp = f.return_vec(trainset['atoms'], [f.rdf_vec])
    n, d = np.shape(train_fp)
    data = np.concatenate((data, train_fp), axis=1)
    assert n == train_size and d == 20
    print('passed rdf_vec')

    # Start testing the standard fingerprint vector generators.
    train_fp = f.return_vec(trainset['atoms'], [f.element_mass_vec])
    n, d = np.shape(train_fp)
    data = np.concatenate((data, train_fp), axis=1)
    assert n == train_size and d == 1
    assert len(f.return_names([f.element_mass_vec])) == d
    print('passed element_mass_vec')

    train_fp = f.return_vec(trainset['atoms'], [f.element_parameter_vec])
    n, d = np.shape(train_fp)
    data = np.concatenate((data, train_fp), axis=1)
    assert n == train_size and d == 4
    assert len(f.return_names([f.element_parameter_vec])) == d
    print('passed element_parameter_vec')

    train_fp = f.return_vec(trainset['atoms'], [f.composition_vec])
    n, d = np.shape(train_fp)
    data = np.concatenate((data, train_fp), axis=1)
    assert n == train_size and d == 2
    assert len(f.return_names([f.composition_vec])) == d
    print('passed composition_vec')

    train_fp = f.return_vec(trainset['atoms'], [f.eigenspectrum_vec])
    n, d = np.shape(train_fp)
    data = np.concatenate((data, train_fp), axis=1)
    assert n == train_size and d == 147
    assert len(f.return_names([f.eigenspectrum_vec])) == d
    print('passed eigenspectrum_vec')

    train_fp = f.return_vec(trainset['atoms'], [f.distance_vec])
    n, d = np.shape(train_fp)
    data = np.concatenate((data, train_fp), axis=1)
    assert n == train_size and d == 2
    assert len(f.return_names([f.distance_vec])) == d
    print('passed distance_vec')

    train_fp = f.return_vec(trainset['atoms'], [
        f.eigenspectrum_vec, f.element_mass_vec, f.composition_vec])
    n, d = np.shape(train_fp)
    assert n == train_size and d == 150
    assert len(f.return_names(
        [f.eigenspectrum_vec, f.element_mass_vec, f.composition_vec])) == d
    print('passed combined generation')

    # Do basic check for atomic porperties.
    no_prop = []
    an_prop = []
    # EXPENSIVE to calculate. Not included in training data.
    for atoms in testset['atoms']:
        no_prop.append(neighbor_features(atoms=atoms))
        an_prop.append(neighbor_features(atoms=atoms,
                                         property=['atomic_number']))
    assert np.shape(no_prop) == (test_size, 15)
    assert np.shape(an_prop) == (test_size, 30)
    print('passed graph_vec')

    return all_cand, data


def cv_test(data):
    """Test some cross-validation."""
    split = k_fold(data, nsplit=5)
    assert len(split) == 5
    for s in split:
        assert len(s) == 10
    split = k_fold(data, nsplit=5, fix_size=5)
    assert len(split) == 5
    for s in split:
        assert len(s) == 5


def db_test(all_cand, data):
    """Test database functions."""
    # Define variables for database to store system descriptors.
    db_name = '/vec_store.sqlite'
    descriptors = ['f' + str(i) for i in range(np.shape(data)[1])]
    targets = ['Energy']
    names = descriptors + targets

    # Set up the database to save system descriptors.
    dd = DescriptorDatabase(db_name=wkdir + db_name, table='FingerVector')
    dd.create_db(names=names)

    # Put data in correct format to be inserted into database.
    print('Generate the database')
    new_data = []
    for i, a in zip(data, all_cand):
        d = []
        d.append(a.info['unique_id'])
        for j in i:
            d.append(j)
        d.append(a.info['key_value_pairs']['raw_score'])
        new_data.append(d)

    # Fill the database with the data.
    dd.fill_db(descriptor_names=names, data=new_data)

    # Test out the database functions.
    train_fingerprint = dd.query_db(names=descriptors)
    train_target = dd.query_db(names=targets)
    print('\nfeature data for candidates:\n', train_fingerprint,
          '\ntarget data for candidates:\n', train_target)

    cand_data = dd.query_db(unique_id='7a216711c2eae02decc04da588c9e592')
    print('\ndata for random candidate:\n', cand_data)

    all_id = dd.query_db(names=['uuid'])
    dd.create_column(new_column=['random'])
    for i in all_id:
        dd.update_descriptor(descriptor='random', new_data=random(),
                             unique_id=i[0])
    print('\nretrieve random vars:\n', dd.query_db(names=['random']))

    print('\nretrieved column names:\n', dd.get_column_names())


if __name__ == '__main__':
    from pyinstrument import Profiler

    profiler = Profiler()
    profiler.start()

    all_cand, data = feature_test()
    cv_test(data)
    db_test(all_cand, data)

    profiler.stop()

    print(profiler.output_text(unicode=True, color=True))

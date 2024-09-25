from unittest import TestCase, main
from random import randint
import sys

sys.path.append('../src')
sys.path.append('src')

import Basefold
from merlin.merlin_transcript import MerlinTranscript
from merkle import MerkleTree

class BasefoldTest(TestCase):
    def test_rep_encode(self):
        self.assertEqual(Basefold.rep_encode([1, 2], 2, 2), [1, 2, 1, 2])
        self.assertEqual(Basefold.rep_encode([1, 2, 3, 4], 2, 3), [1, 2, 1, 2, 1, 2, 3, 4, 3, 4, 3, 4])
        
    def test_rep_encode_invalid_input(self):
        with self.assertRaises(AssertionError):
            Basefold.rep_encode([1, 2], 0, 2)
        
        with self.assertRaises(AssertionError):
            Basefold.rep_encode([1, 2], 2, 0)
        
        with self.assertRaises(AssertionError):
            Basefold.rep_encode([1, 2], -1, 2)
        
        with self.assertRaises(AssertionError):
            Basefold.rep_encode([1, 2], 2, -1)

    def test_rs_encode_single(self):
        m = [1, 2, 3]
        alpha = [0, 1, 2, 3, 4, 5]
        c = 2
        result = Basefold.rs_encode_single(m, alpha, c)
        self.assertEqual(result, [1, 6, 17, 34, 57, 86])

    def test_rs_encode(self):
        m = [1, 2, 3, 4, 5, 6]
        k0 = 3
        c = 2
        result = Basefold.rs_encode(m, k0, c)
        self.assertEqual(result, [1, 6, 17, 34, 57, 86, 4, 15, 38, 73, 120, 179])

    def test_basefold_encode(self):
        m = [1, 2, 3, 4]
        k0 = 2
        depth = 1
        c = 2
        T = [[1, 2, 3, 4]]
        result = Basefold.basefold_encode(m, k0, depth, c, T)
        self.assertEqual(result, [4, 10, 10, 18, -2, -6, -8, -14])

    def test_query_phase(self):
        num_vars = 2 ** randint(0, 4)
        transcript = MerlinTranscript(b"test")
        first_oracle = [randint(0, 100) for _ in range(2 ** num_vars)]
        first_tree = MerkleTree(first_oracle)
        oracles = []
        trees = []
        num_vars_copy = num_vars - 1
        while num_vars_copy > 0:
            oracles.append([randint(0, 100) for _ in range(2 ** num_vars_copy)])
            trees.append(MerkleTree(oracles[-1]))
            num_vars_copy -= 1
        num_verifier_queries = randint(0, 16)
        query_paths, merkle_paths = Basefold.query_phase(transcript, first_tree, first_oracle, trees, oracles, num_vars, num_verifier_queries)
        self.assertEqual(len(query_paths), num_verifier_queries)
        self.assertEqual(len(merkle_paths), num_verifier_queries)

    def test_basefold(self):
        for i in range(100):
            num_vars = randint(1, 5)
            blowup_factor = randint(1, 4)
            depth = num_vars
            k = depth
            num_verifier_queries = randint(0, 8)
            us = [randint(0, 100) for _ in range(num_vars)]
            f_evals = [randint(0, 100) for _ in range(2 ** num_vars)]
            v = Basefold.mle_eval_from_evals(f_evals, us)

            params = {
                'num_vars': num_vars,
                'blowup_factor': blowup_factor,
                'depth': depth,
                'k': k,
                'num_verifier_queries': num_verifier_queries,
                'us': us,
                'f_evals': f_evals,
                'v': v
            }
            print(f'{i}th test, params:{params}')

            T = []
            cnt = 0
            k0 = 2 ** (num_vars - depth)
            for i in range(depth):
                T.append([randint(1, 100) for j in range(k0 * blowup_factor * 2 ** i)])
                cnt += len(T[-1])

            f_code = Basefold.basefold_encode(m=f_evals, k0=k0, depth=depth, c=blowup_factor, T=T, G0=Basefold.rs_encode)
            commit = MerkleTree(f_code)
            
            transcript = MerlinTranscript(b"verify queries")
            transcript.append_message(b"commit.root", bytes(commit.root, 'ascii'))
            proof = Basefold.prove_basefold_evaluation_arg_multilinear_basis(f_code, f_evals, us, v, k, k0, T, blowup_factor, commit, num_verifier_queries, transcript)
            self.assertTrue(Basefold.verify_basefold_evaluation_arg_multilinear_basis(2 ** num_vars * blowup_factor, commit, proof, us, v, 2, k, T, blowup_factor, num_verifier_queries))

    def test_basefold_fri_monomial_basis(self):
        vs = [1, 2, 3, 4]
        table = [1, 2]
        alpha = 2
        result = Basefold.basefold_fri_monomial_basis(vs, table, alpha)
        self.assertEqual(len(result), 2)

    def test_basefold_fri_multilinear_basis(self):
        vs = [1, 2, 3, 4]
        table = [1, 2]
        c = 2
        result = Basefold.basefold_fri_multilinear_basis(vs, table, c)
        self.assertEqual(len(result), 2)


if __name__ == '__main__':
    main()

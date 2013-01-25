cntnt
=====

A pure content management system with a different approach. Every node has a
named relation with an other node. And nodes have types which defines the
structure and relations of a node.

This is actually an experiment project I've started years before.

For understanding what this does, just try running cntnt.py:

.. code-block::

    $ ./cntnt.py
    Usage:
                Create   -c --content --type --parent [--label]
                  Read   -r (--id|--path)
           Read Childs   -R --id
                Update   -u --id [--content] [--type] [--parent] [--label]
                Delete   -d --id
      Recursive Delete   -D --id
                  Tree   -t [--id]


# -*- coding: utf-8 -*-
from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup

setup(name             = "AutoAE",
      version          = "0.0.1",
      author           = ["Artem Revenko"],
      author_email     = ["artreven@gmail.com"],
      description      = "Python package for doing attribute exploration automatically",
      keywords         = ["Computer Science", "Artificial Intelligence",
                          "Formal Concept Analysis", "Implications", "Concept Lattice",
                          "Computational Logic"]
)
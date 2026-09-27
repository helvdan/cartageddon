"""Модуль для очистки и обработки иерархии категорий (стадия HIERARCHY).

Этот модуль отвечает за удаление избыточных связей товаров с родительскими
категориями, оставляя привязку только к самым глубоким (конечным) подкатегориям.
"""
import logging
from artifacts import ParquetArtifact
from stages.base import Stage

from typing import Dict


class ReduceStage(Stage):
    artifact_cls = ParquetArtifact
    is_mandatory: bool = False
    name = "REDUCE"
    postfix = "reduced"
    logger = logging.getLogger(name)

    def run(self, artifacts: Dict[str, ParquetArtifact]) -> Dict[str, ParquetArtifact]:
        output: Dict[str, ParquetArtifact] = artifacts.copy()
        a = artifacts['oc_product_to_category']
        a = a.reduce_hierarchy(
            category_artifact=artifacts['oc_category'],
            product_id_col='product_id',
            category_id_col='category_id',
            parent_id_col='parent_id',
        )
        n = self.create_artifact("oc_product_to_category")
        n.save(a.data)
        output['oc_product_to_category'] = n
        return output

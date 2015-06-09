# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from django.core import management
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType

from ralph.assets.models.assets import (
    AssetModel,
    Environment,
    Service,
    ServiceEnvironment
)
from ralph.assets.models.choices import ObjectModelType
from ralph.back_office.models import (
    BackOfficeAsset,
    Warehouse
)
from ralph.data_center.models.physical import (
    DataCenter,
    Rack,
    ServerRoom
)
from ralph.data_center.tests.factories import (
    DataCenterFactory
)
from ralph.data_importer.management.commands import importer
from ralph.data_importer.resources import AssetModelResource
from ralph.data_importer.models import ImportedObjects


class DataImporterTestCase(TestCase):

    """TestCase data importer command."""

    def setUp(self):
        self.base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        asset_model = AssetModel()
        asset_model.name = "asset_model_1"
        asset_model.type = ObjectModelType.back_office
        asset_model.save()
        asset_content_type = ContentType.objects.get_for_model(AssetModel)
        ImportedObjects.objects.create(
            content_type=asset_content_type,
            object_pk=asset_model.pk,
            old_object_pk=1
        )

        warehouse = Warehouse()
        warehouse.name = "warehouse_1"
        warehouse.save()

        warehouse_content_type = ContentType.objects.get_for_model(Warehouse)
        ImportedObjects.objects.create(
            content_type=warehouse_content_type,
            object_pk=warehouse.pk,
            old_object_pk=1
        )

        environment = Environment()
        environment.name = "environment_1"
        environment.save()

        service = Service()
        service.name = "service_1"
        service.save()

        service_environment = ServiceEnvironment()
        service_environment.environment = environment
        service_environment.service = service
        service_environment.save()

    def test_get_resource(self):
        """Test get resources method."""
        asset_model_resource = importer.get_resource('AssetModel')
        self.assertIsInstance(asset_model_resource, AssetModelResource)

    def test_importer_command_warehouse(self):
        """Test importer management command with Warehouse model."""
        warehouse_csv = os.path.join(
            self.base_dir,
            'tests/samples/warehouses.csv'
        )
        management.call_command(
            'importer',
            'Warehouse',
            warehouse_csv,
            '--noinput'
        )
        self.assertTrue(Warehouse.objects.filter(
            name="Poznań").exists()
        )

    def test_importer_command_back_office_asset(self):
        """Test importer management command with BackOfficeAsset model."""
        back_office_csv = os.path.join(
            self.base_dir,
            'tests/samples/back_office_assets.csv'
        )
        management.call_command(
            'importer',
            'BackOfficeAsset',
            back_office_csv,
            '--noinput'
        )
        self.assertTrue(BackOfficeAsset.objects.filter(
            sn="bo_asset_sn").exists()
        )
        back_office_asset = BackOfficeAsset.objects.get(sn="bo_asset_sn")
        self.assertEqual(
            back_office_asset.warehouse.name,
            "warehouse_1"
        )
        self.assertEqual(
            back_office_asset.model.name,
            "asset_model_1"
        )
        self.assertEqual(
            back_office_asset.service_env.service.name,
            "service_1"
        )

    def test_importer_command_with_tab(self):
        """Test importer management command with Warehouse model and
        tab separation file
        """
        warehouse_csv = os.path.join(
            self.base_dir,
            'tests/samples/warehouses_tab.csv'
        )
        management.call_command(
            'importer',
            'Warehouse',
            warehouse_csv,
            '--noinput',
            delimiter='\t',
        )
        self.assertTrue(Warehouse.objects.filter(
            name="Barcelona").exists()
        )

    def test_importer_command_with_skipid(self):
        """Test importer management command with Warehouse model and
        tab separation file
        """
        warehouse_csv = os.path.join(
            self.base_dir,
            'tests/samples/warehouses_skipid.csv'
        )
        management.call_command(
            'importer',
            'Warehouse',
            warehouse_csv,
            '--noinput',
            '--skipid',
            delimiter=',',
        )
        warehouse = Warehouse.objects.filter(name="Cupertino").first()
        self.assertNotEqual(warehouse.pk, 200)

        warehouse_content_type = ContentType.objects.get_for_model(Warehouse)
        warehouse_exists = ImportedObjects.objects.filter(
            content_type=warehouse_content_type,
            old_object_pk=200
        ).exists()
        self.assertTrue(warehouse_exists)


    def test_importer_command_with_semicolon(self):
        """Test importer management command with Warehouse model and
        semicolon separation file
        """
        warehouse_csv = os.path.join(
            self.base_dir,
            'tests/samples/warehouses_semicolon.csv'
        )
        management.call_command(
            'importer',
            'Warehouse',
            warehouse_csv,
            '--noinput',
            delimiter=';',
        )
        self.assertTrue(Warehouse.objects.filter(
            name="Berlin").exists()
        )

    def test_imported_object(self):
        """Test importer management command with ImportedObjects model."""
        data_center = DataCenterFactory(name='CSV_test')
        data_center_content_type = ContentType.objects.get_for_model(
            DataCenter
        )
        ImportedObjects.objects.create(
            content_type=data_center_content_type,
            object_pk=data_center.pk,
            old_object_pk=1
        )
        server_room_csv = os.path.join(
            self.base_dir,
            'tests/samples/server_room.csv'
        )
        rack_csv = os.path.join(
            self.base_dir,
            'tests/samples/rack.csv'
        )
        management.call_command(
            'importer',
            'ServerRoom',
            server_room_csv,
            '--noinput',
            delimiter=',',
        )

        content_type = ContentType.objects.get_for_model(ServerRoom)
        imported_object_exists = ImportedObjects.objects.filter(
            content_type=content_type,
            old_object_pk=1
        ).exists()
        self.assertTrue(imported_object_exists)

        management.call_command(
            'importer',
            'Rack',
            rack_csv,
            '--noinput',
            delimiter=',',
        )
        self.assertTrue(Rack.objects.filter(
            name="Rack_csv_test").exists()
        )

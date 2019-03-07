from HttpHelper import HTTP
from django.db import transaction
from huub_utils.schema_validator import SchemaValidator, SchemaException
from rest_framework.viewsets import ModelViewSet

from aggregation_service_api.models import Aggregation, AggregationUnit, AggregationPack
from aggregation_service_api.utils.utils import get_schema_full_path


class AggregationView(ModelViewSet):

    def insert_aggregation(self, request):
        try:
            SchemaValidator.validate_json_structure(request.data, get_schema_full_path('POST_insert_aggregation'))
        except SchemaException as e:
            return HTTP.response(e.code, e.details)

        aggregation_unit_id = request.data['aggregation_unit_id']
        pack_ean = request.data['pack_ean']

        try:
            aggregation_unit = AggregationUnit.objects.prefetch_related(
                'aggregation_unit__aggregation_pack'
            ).get(id=aggregation_unit_id)
            pack = AggregationPack.objects.get(ean=pack_ean)
            if Aggregation.objects.is_pack_picked(pack):
                return HTTP.response(400, 'Pack Is Already Associated')

            with transaction.atomic():
                Aggregation.objects.create(
                    aggregation_unit=aggregation_unit,
                    aggregation_pack=pack
                )
                aggregation_unit.total_packs = aggregation_unit.total_packs + 1
                aggregation_unit.save()

        except AggregationPack.DoesNotExist:
            return HTTP.response(400, 'Invalid Pack')
        except Exception as e:
            return HTTP.response(400, 'Error: {}'.format(str(e)))

        return HTTP.response(200, 'Pack Associated')

    def delete_aggregation(self, request):
        try:
            pack_ean = request.query_params['pack_ean']
            aggregation_unit_id = request.query_params['aggregation_unit_id']
        except KeyError:
            return HTTP.response(400, 'Missing URL parameters: pack_ean; aggregation_unit_id')

        try:
            with transaction.atomic():
                aggregation = Aggregation.objects.select_related('aggregation_unit', 'aggregation_pack').filter(
                    aggregation_unit__id=aggregation_unit_id,
                    aggregation_pack__ean=pack_ean
                ).get()

                aggregation.aggregation_unit.total_packs -= 1
                aggregation.aggregation_unit.save()
                aggregation.delete()

        except Aggregation.DoesNotExist:
            return HTTP.response(404, 'There is no association between Aggregation Unit and the Ean provided.')
        except Exception as e:
            return HTTP.response(400, 'Error: {}'.format(str(e)))

        return HTTP.response(200, 'Pack Deleted')

#
# Copyright (c) 2017 nexB Inc. and others. All rights reserved.
# http://nexb.com and https://github.com/nexB/vulnerablecode/
# The VulnerableCode software is licensed under the Apache License version 2.0.
# Data generated with VulnerableCode require an acknowledgment.
#
# You may not use this software except in compliance with the License.
# You may obtain a copy of the License at: http://apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
# When you publish or redistribute any data created with VulnerableCode or any VulnerableCode
# derivative work, you must accompany this data with the following acknowledgment:
#
#  Generated with VulnerableCode and provided on an "AS IS" BASIS, WITHOUT WARRANTIES
#  OR CONDITIONS OF ANY KIND, either express or implied. No content created from
#  VulnerableCode should be considered or used as legal advice. Consult an Attorney
#  for any legal advice.
#  VulnerableCode is a free software code scanning tool from nexB Inc. and others.
#  Visit https://github.com/nexB/vulnerablecode/ for support and download.

import json
import os

from django.test import TestCase

from vulnerabilities.api import PackageSerializer
from vulnerabilities.data_dump import debian_dump
from vulnerabilities.data_dump import ubuntu_dump
from vulnerabilities.models import Package
from vulnerabilities.scraper import debian
from vulnerabilities.scraper import ubuntu


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA = os.path.join(BASE_DIR, 'test_data/')


class TestDebianResponse(TestCase):
    @classmethod
    def setUpTestData(cls):
        with open(os.path.join(TEST_DATA, 'debian.json')) as f:
            test_data = json.load(f)

        extract_data = debian.extract_vulnerabilities(test_data)
        debian_dump(extract_data)

    def setUp(self):
        self.response = self.client.get('/api/packages/?name=mimetex', format='json').data

    def test_count(self):
        self.assertEqual(4, self.response['count'])

    def test_name(self):
        first_result = self.response['results'][0]
        self.assertEqual('mimetex', first_result['name'])

    def test_version(self):
        versions = {r['version'] for r in self.response['results']}
        self.assertIn('1.50-1.1', versions)
        self.assertIn('1.74-1', versions)

    def test_packageurl(self):
        purls = {r['package_url'] for r in self.response['results']}
        self.assertIn('pkg:deb/debian/mimetex@1.50-1.1?distro=jessie', purls)
        self.assertIn('pkg:deb/debian/mimetex@1.74-1?distro=jessie', purls)


class TestUbuntuResponse(TestCase):
    def test_ubuntu_response(self):
        with open(os.path.join(TEST_DATA, 'ubuntu_main.html')) as f:
            test_data = f.read()

        extract_data = ubuntu.extract_cves(test_data)
        ubuntu_dump(extract_data)
        response = self.client.get('/api/packages/?name=automake', format='json')

        result = response.data.get('results')[0]
        self.assertEqual('automake', result['name'])
        self.assertEqual(None, result['version'])
        self.assertEqual(1, len(result['vulnerabilities']))

        vuln = result['vulnerabilities'][0]
        self.assertEqual(1, len(vuln['references']))
        self.assertEqual('CVE-2012-3386', vuln['references'][0]['reference_id'])


class TestSerializers(TestCase):
    @classmethod
    def setUpTestData(cls):
        with open(os.path.join(TEST_DATA, 'debian.json')) as f:
            test_data = json.load(f)

        extract_data = debian.extract_vulnerabilities(test_data)
        debian_dump(extract_data)

    def test_package_serializer(self):
        pk = Package.objects.filter(name="mimetex")
        response = PackageSerializer(pk, many=True).data

        self.assertEqual(4, len(response))

        first_result = response[0]
        self.assertEqual('mimetex', first_result['name'])

        versions = {r['version'] for r in response}
        self.assertIn('1.50-1.1', versions)
        self.assertIn('1.74-1', versions)

        purls = {r['package_url'] for r in response}
        self.assertIn('pkg:deb/debian/mimetex@1.50-1.1?distro=jessie', purls)
        self.assertIn('pkg:deb/debian/mimetex@1.74-1?distro=jessie', purls)

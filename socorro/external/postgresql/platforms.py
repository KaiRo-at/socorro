# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
from socorro.external.postgresql.base import PostgreSQLBase

logger = logging.getLogger("webapi")


class Platforms(PostgreSQLBase):
    """Implement the /platforms service with PostgreSQL. """

    def get(self, **kwargs):
        """Return data about all platforms. """
        sql = """/* socorro.external.postgresql.platforms.Platforms.get */
            SELECT
                os_name AS name,
                os_short_name AS code
            FROM os_names
        """

        error_message = "Failed to retrieve platforms data from PostgreSQL"
        results = self.query(sql, error_message=error_message)

        platforms = results.zipped()

        return {
            "hits": platforms,
            "total": len(platforms)
        }

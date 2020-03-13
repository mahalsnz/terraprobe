# Generated by Django 2.2.1 on 2019-07-28 23:23

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [('skeleton', '0001_initial')]

    operations = [
        migrations.RunSQL(
        '''
            CREATE OR REPLACE VIEW skeleton_season_start_end AS
            SELECT
                season_start.season_id,
                season_start.season_name,
                season_start.site_id,
                season_start.site_name,
                season_start.type_name AS start_name,
                season_start.type_id AS start_id,
                season_start.date AS period_from,
                season_end.type_name AS end_name,
                season_end.type_id AS end_id,
                season_end.date AS period_to
            FROM
            (
                SELECT
                skeleton_season.name AS season_name,
                skeleton_season.id AS season_id,
                skeleton_site.name AS site_name,
                skeleton_site.id AS site_id,
                skeleton_criticaldate.date,
                skeleton_criticaldatetype.name AS type_name,
                skeleton_criticaldatetype.id AS type_id
                FROM
                    skeleton_season
                    LEFT JOIN skeleton_criticaldate ON skeleton_criticaldate.season_id = skeleton_season.id
                    LEFT JOIN skeleton_criticaldatetype ON skeleton_criticaldatetype.id = skeleton_criticaldate.type_id
                    LEFT JOIN skeleton_site ON skeleton_site.id = skeleton_criticaldate.site_id
                WHERE
                skeleton_criticaldatetype.season_flag = TRUE AND
                skeleton_criticaldatetype.name = 'Start'
            ) AS season_start
            ---------
            LEFT JOIN
            ---------
            (
                SELECT
                    skeleton_season.name,
                    skeleton_season.id AS season_id,
                    skeleton_site.name,
                    skeleton_site.id AS site_id,
                    skeleton_criticaldate.date,
                    skeleton_criticaldatetype.name AS type_name,
                    skeleton_criticaldatetype.id AS type_id
                FROM
                    skeleton_season
                    LEFT JOIN skeleton_criticaldate ON skeleton_criticaldate.season_id = skeleton_season.id
                    LEFT JOIN skeleton_criticaldatetype ON skeleton_criticaldatetype.id = skeleton_criticaldate.type_id
                    LEFT JOIN skeleton_site ON skeleton_site.id = skeleton_criticaldate.site_id
                WHERE
                    skeleton_criticaldatetype.season_flag = TRUE AND
                    skeleton_criticaldatetype.name = 'End'
            ) season_end
            ON season_start.site_id = season_end.site_id AND season_start.season_id = season_end.season_id;
        '''
        )

    ]

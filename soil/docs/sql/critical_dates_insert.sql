INSERT INTO skeleton_criticaldate (
SELECT
	nextval('skeleton_criticaldate_id_seq') as id,
	date + interval '1 year' AS date,
	comment,
	CURRENT_TIMESTAMP as created_date,
	created_by_id,
	2 as season_id,
	site_id,
	type_id
FROM
	skeleton_criticaldate
WHERE
	skeleton_criticaldate.season_id = 1
);

COMMIT;
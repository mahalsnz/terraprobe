INSERT INTO skeleton_kcreading (
SELECT
	nextval('skeleton_kcreading_id_seq') as id,
	CAST(period_from + interval '1 year' as date) AS period_from,
	CAST(period_to + interval '1 year' as date) AS period_to,
	kc,
	CURRENT_TIMESTAMP as created_date,
	created_by_id,
	crop_id
FROM
	skeleton_kcreading
WHERE
	skeleton_kcreading.crop_id = 1
);
-- Run for 1, 2, 4 and 8 crop id
COMMIT;

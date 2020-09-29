INSERT INTO skeleton_reading
(
id,
date,
depth1,
depth2,
depth3,
depth4,
depth5,
depth6,
depth7,
depth8,
depth9,
depth10,
rz1,
rz2,
rz3,
created_date,
created_by_id,
serial_number_id,
site_id,
type_id
)

(
SELECT
	nextval('skeleton_reading_id_seq') as id,
	CAST(date + interval '1 year' as date) AS date,
	depth1,
	depth2,
	depth3,
	depth4,
	depth5,
	depth6,
	depth7,
	depth8,
	depth9,
	depth10,
	rz1,
	rz2,
	rz3,
	CURRENT_TIMESTAMP as created_date,
	created_by_id,
	serial_number_id,
	site_id,
	type_id
FROM
	skeleton_reading
WHERE
	skeleton_reading.type_id In (2, 3)
);

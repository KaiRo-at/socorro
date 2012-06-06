\set ON_ERROR_STOP 1

BEGIN;

CREATE TEMPORARY TABLE 
ON COMMIT DROP old_versions (
	build_id numeric,
	product citext,
	version text,
	platform citext
);

\copy old_versions FROM 'old_releases.csv' with csv header

-- insert all "aurora" versions -- basically any development nonbeta

CREATE TEMPORARY TABLE missing_versions
ON COMMIT DROP
AS SELECT productdims.product::citext as product, 
	productdims.version::citext as version
FROM productdims LEFT OUTER JOIN product_versions
	ON productdims.product::citext = product_versions.product_name
	AND productdims.version::citext = product_versions.version_string
WHERE product_versions.product_name is NULL;

INSERT INTO product_versions ( 
	product_version_id,
	product_name,
	major_version,
	release_version,
	version_string,
	beta_number,
	version_sort,
	build_date,
	sunset_date,
	build_type )
SELECT id,
	productdims.product,
	to_major_version(productdims.version),
	productdims.version,
	productdims.version,
	null,
	old_version_sort(productdims.version),
	start_date,
	end_date,
	'Aurora'
FROM productdims JOIN product_visibility
	ON productdims.id = product_visibility.productdims_id
	JOIN missing_versions 
		on productdims.version = missing_versions.version
		AND productdims.product = missing_versions.product
WHERE
	release IN ( 'milestone', 'development' )
	and productdims.version !~ $x$\db\d$x$;
	
-- insert all beta versions

INSERT INTO product_versions ( 
	product_version_id,
	product_name,
	major_version,
	release_version,
	version_string,
	beta_number,
	version_sort,
	build_date,
	sunset_date,
	build_type )
SELECT id,
	productdims.product,
	to_major_version(productdims.version),
	productdims.version,
	productdims.version,
	substring(version from $x$\db(\d+)$x$)
	old_version_sort(productdims.version),
	start_date,
	end_date,
	'Beta'
FROM productdims JOIN product_visibility
	ON productdims.id = product_visibility.productdims_id
	JOIN missing_versions 
		on productdims.version = missing_versions.version
		AND productdims.product = missing_versions.product
WHERE
	productdims.version ~ $x$\db\d$x$;

-- insert all release versions

INSERT INTO product_versions ( 
	product_version_id,
	product_name,
	major_version,
	release_version,
	version_string,
	beta_number,
	version_sort,
	build_date,
	sunset_date,
	build_type )
SELECT id,
	productdims.product,
	to_major_version(productdims.version),
	productdims.version,
	productdims.version,
	null,
	old_version_sort(productdims.version),
	start_date,
	end_date,
	'Release'
FROM productdims JOIN product_visibility
	ON productdims.id = product_visibility.productdims_id
	JOIN missing_versions 
		on productdims.version = missing_versions.version
		AND productdims.product = missing_versions.product
WHERE
	release = 'release'
	and productdims.version !~ $x$\db\d$x$;

-- insert builds

INSERT INTO product_version_builds (
	product_verson_id,
	build_id,
	platform,
	repository )
SELECT product_version_id,
	build_id,
	platform,
	'release'
FROM missing_versions JOIN product_versions
	ON missing_versions.product = product_name
	AND missing_versions.version = version_string
	JOIN old_versions
	USING (product, version);
	
COMMIT;




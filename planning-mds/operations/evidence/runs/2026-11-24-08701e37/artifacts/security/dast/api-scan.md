# ZAP Scanning Report

ZAP by [Checkmarx](https://checkmarx.com/).


## Summary of Alerts

| Risk Level | Number of Alerts |
| --- | --- |
| High | 0 |
| Medium | 0 |
| Low | 0 |
| Informational | 3 |




## Insights

| Level | Reason | Site | Description | Statistic |
| --- | --- | --- | --- | --- |
| Medium | Exceeded High | http://brain-f0009-08701e37-engine-validation-1:8000 | Percentage of responses with status code 4xx | 99 % |
| Info | Informational | http://brain-f0009-08701e37-engine-validation-1:8000 | Percentage of endpoints with content type application/json | 54 % |
| Info | Informational | http://brain-f0009-08701e37-engine-validation-1:8000 | Percentage of endpoints with content type application/problem+json | 45 % |
| Info | Informational | http://brain-f0009-08701e37-engine-validation-1:8000 | Percentage of endpoints with method GET | 75 % |
| Info | Informational | http://brain-f0009-08701e37-engine-validation-1:8000 | Percentage of endpoints with method POST | 25 % |
| Info | Informational | http://brain-f0009-08701e37-engine-validation-1:8000 | Count of total endpoints | 44    |







## Alerts

| Name | Risk Level | Number of Instances |
| --- | --- | --- |
| A Client Error response code was returned by the server | Informational | 43 |
| Non-Storable Content | Informational | Systemic |
| Storable and Cacheable Content | Informational | 2 |




## Alert Detail



### [ A Client Error response code was returned by the server ](https://www.zaproxy.org/docs/alerts/100000/)



##### Informational (High)

### Description

A response code of 401 was returned by the server.
This may indicate that the application is failing to handle unexpected input correctly.
Raised by the 'Alert on HTTP Response Code Error' script

* URL: http://brain-f0009-08701e37-engine-validation-1:8000
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/1163215350232168264
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/1163215350232168264`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/content
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/content`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/content/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/content/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/content/8583479571984404517
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/content/8583479571984404517`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/7028507620513289098
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/7028507620513289098`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/files/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/files/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/files/1785741165639177382
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/files/1785741165639177382`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/files/path
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/files/path`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/files/path/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/files/path/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/facts
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/facts`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/facts/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/facts/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/facts/3689563327546377163
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/facts/3689563327546377163`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId%3FvalidAsOf=validAsOf&knownAsOf=knownAsOf
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId (knownAsOf,validAsOf)`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId/6300241848586593541
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId/6300241848586593541`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId/actuator/health
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId/actuator/health`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/3039552527898730860
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/3039552527898730860`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/2803402873098797947
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/2803402873098797947`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/reviewBatchId
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/reviewBatchId`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/reviewBatchId/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/reviewBatchId/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/reviewBatchId/4813827209091779815
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/reviewBatchId/4813827209091779815`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/reviewItemId
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/reviewItemId`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/reviewItemId/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/reviewItemId/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/computeMetadata/v1/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/computeMetadata/v1/ ()({artifact_created_at,assertion_created_at,change_reason,evidence_refs:[],expected_current_version_id,idempotency_key,review_decision_id,source_received_at,temporal:{John Doe},valid_from,valid_to,value})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId/commits
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId/commits ()({artifact_created_at,assertion_created_at,change_reason,evidence_refs:[],expected_current_version_id,idempotency_key,review_decision_id,source_received_at,temporal:{John Doe},valid_from,valid_to,value})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId/commits/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId/commits/ ()({artifact_created_at,assertion_created_at,change_reason,evidence_refs:[],expected_current_version_id,idempotency_key,review_decision_id,source_received_at,temporal:{John Doe},valid_from,valid_to,value})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/latest/meta-data/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/latest/meta-data/ ()({artifact_created_at,assertion_created_at,change_reason,evidence_refs:[],expected_current_version_id,idempotency_key,review_decision_id,source_received_at,temporal:{John Doe},valid_from,valid_to,value})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/metadata/instance
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/metadata/instance ()({artifact_created_at,assertion_created_at,change_reason,evidence_refs:[],expected_current_version_id,idempotency_key,review_decision_id,source_received_at,temporal:{John Doe},valid_from,valid_to,value})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/metadata/v1
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/metadata/v1 ()({artifact_created_at,assertion_created_at,change_reason,evidence_refs:[],expected_current_version_id,idempotency_key,review_decision_id,source_received_at,temporal:{John Doe},valid_from,valid_to,value})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/opc/v1/instance/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/opc/v1/instance/ ()({artifact_created_at,assertion_created_at,change_reason,evidence_refs:[],expected_current_version_id,idempotency_key,review_decision_id,source_received_at,temporal:{John Doe},valid_from,valid_to,value})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/opc/v2/instance/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/opc/v2/instance/ ()({artifact_created_at,assertion_created_at,change_reason,evidence_refs:[],expected_current_version_id,idempotency_key,review_decision_id,source_received_at,temporal:{John Doe},valid_from,valid_to,value})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/openstack/latest/meta_data.json
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/openstack/latest/meta_data.json ()({artifact_created_at,assertion_created_at,change_reason,evidence_refs:[],expected_current_version_id,idempotency_key,review_decision_id,source_received_at,temporal:{John Doe},valid_from,valid_to,value})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `404`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/reviewBatchId/decisions
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/reviewBatchId/decisions ()({decisions:[{action,assertion_version,corrected_assertion_id,corrected_value,decided_at,event_sha256,evidence,id,reason_code,review_batch_id,review_item_id,reviewer_comment,reviewer_principal_id,stale}]})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/reviewBatchId/decisions/
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/reviewBatchId/decisions/ ()({decisions:[{action,assertion_version,corrected_assertion_id,corrected_value,decided_at,event_sha256,evidence,id,reason_code,review_batch_id,review_item_id,reviewer_comment,reviewer_principal_id,stale}]})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``


Instances: 43

### Solution



### Reference



#### CWE Id: [ 388 ](https://cwe.mitre.org/data/definitions/388.html)


#### WASC Id: 20

#### Source ID: 4

### [ Non-Storable Content ](https://www.zaproxy.org/docs/alerts/10049/)



##### Informational (Medium)

### Description

The response contents are not storable by caching components such as proxy servers. If the response does not contain sensitive, personal or user-specific information, it may benefit from being stored and cached, to improve performance.

* URL: http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/files/path
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/content/artifactId/files/path`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/reviewItemId
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/reviewItemId`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId/commits
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/facts/factSlotId/commits ()({artifact_created_at,assertion_created_at,change_reason,evidence_refs:[],expected_current_version_id,idempotency_key,review_decision_id,source_received_at,temporal:{John Doe},valid_from,valid_to,value})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/reviewBatchId/decisions
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/reviews/batches/reviewBatchId/decisions ()({decisions:[{action,assertion_version,corrected_assertion_id,corrected_value,decided_at,event_sha256,evidence,id,reason_code,review_batch_id,review_item_id,reviewer_comment,reviewer_principal_id,stale}]})`
  * Method: `POST`
  * Parameter: ``
  * Attack: ``
  * Evidence: `401`
  * Other Info: ``

Instances: Systemic


### Solution

The content may be marked as storable by ensuring that the following conditions are satisfied:
The request method must be understood by the cache and defined as being cacheable ("GET", "HEAD", and "POST" are currently defined as cacheable)
The response status code must be understood by the cache (one of the 1XX, 2XX, 3XX, 4XX, or 5XX response classes are generally understood)
The "no-store" cache directive must not appear in the request or response header fields
For caching by "shared" caches such as "proxy" caches, the "private" response directive must not appear in the response
For caching by "shared" caches such as "proxy" caches, the "Authorization" header field must not appear in the request, unless the response explicitly allows it (using one of the "must-revalidate", "public", or "s-maxage" Cache-Control response directives)
In addition to the conditions above, at least one of the following conditions must also be satisfied by the response:
It must contain an "Expires" header field
It must contain a "max-age" response directive
For "shared" caches such as "proxy" caches, it must contain a "s-maxage" response directive
It must contain a "Cache Control Extension" that allows it to be cached
It must have a status code that is defined as cacheable by default (200, 203, 204, 206, 300, 301, 404, 405, 410, 414, 501).

### Reference


* [ https://datatracker.ietf.org/doc/html/rfc7234 ](https://datatracker.ietf.org/doc/html/rfc7234)
* [ https://datatracker.ietf.org/doc/html/rfc7231 ](https://datatracker.ietf.org/doc/html/rfc7231)
* [ https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html ](https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html)


#### CWE Id: [ 524 ](https://cwe.mitre.org/data/definitions/524.html)


#### WASC Id: 13

#### Source ID: 3

### [ Storable and Cacheable Content ](https://www.zaproxy.org/docs/alerts/10049/)



##### Informational (Medium)

### Description

The response contents are storable by caching components such as proxy servers, and may be retrieved directly from the cache, rather than from the origin server by the caching servers, in response to similar requests from other users. If the response data is sensitive, personal or user-specific, this may result in sensitive information being leaked. In some cases, this may even result in a user gaining complete control of the session of another user, depending on the configuration of the caching components in use in their environment. This is primarily an issue where "shared" caching servers such as "proxy" caches are configured on the local network. This configuration is typically found in corporate or educational environments, for instance.

* URL: http://brain-f0009-08701e37-engine-validation-1:8000/health
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/health`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: `In the absence of an explicitly specified caching lifetime directive in the response, a liberal lifetime heuristic of 1 year was assumed. This is permitted by rfc7234.`
* URL: http://brain-f0009-08701e37-engine-validation-1:8000/openapi.json
  * Node Name: `http://brain-f0009-08701e37-engine-validation-1:8000/openapi.json`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: `In the absence of an explicitly specified caching lifetime directive in the response, a liberal lifetime heuristic of 1 year was assumed. This is permitted by rfc7234.`


Instances: 2

### Solution

Validate that the response does not contain sensitive, personal or user-specific information. If it does, consider the use of the following HTTP response headers, to limit, or prevent the content being stored and retrieved from the cache by another user:
Cache-Control: no-cache, no-store, must-revalidate, private
Pragma: no-cache
Expires: 0
This configuration directs both HTTP 1.0 and HTTP 1.1 compliant caching servers to not store the response, and to not retrieve the response (without validation) from the cache, in response to a similar request.

### Reference


* [ https://datatracker.ietf.org/doc/html/rfc7234 ](https://datatracker.ietf.org/doc/html/rfc7234)
* [ https://datatracker.ietf.org/doc/html/rfc7231 ](https://datatracker.ietf.org/doc/html/rfc7231)
* [ https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html ](https://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html)


#### CWE Id: [ 524 ](https://cwe.mitre.org/data/definitions/524.html)


#### WASC Id: 13

#### Source ID: 3



-- SQL script to list and approve annotators

-- First, let's see all pending annotators
SELECT 
    ap.id,
    u.email,
    u.first_name || ' ' || u.last_name AS full_name,
    ap.status,
    ap.email_verified,
    ap.applied_at,
    ap.approved_at
FROM annotator_profile ap
JOIN users_user u ON ap.user_id = u.id
WHERE ap.status IN ('pending_verification', 'pending_test', 'test_submitted', 'under_review')
ORDER BY ap.applied_at DESC;

-- List tests
SELECT 
    at.id,
    u.email,
    at.test_type,
    at.status AS test_status,
    at.submitted_at,
    at.accuracy
FROM annotation_test at
JOIN annotator_profile ap ON at.annotator_id = ap.id
JOIN users_user u ON ap.user_id = u.id
WHERE at.status IN ('pending', 'in_progress', 'submitted')
ORDER BY at.submitted_at DESC;

-- To approve an annotator, you'll need to run these commands:
-- Replace <email> with the actual email

-- UPDATE annotation_test at
-- SET 
--     status = 'passed',
--     accuracy = 100.00,
--     evaluated_at = NOW(),
--     feedback = 'Test approved by admin'
-- FROM annotator_profile ap
-- JOIN users_user u ON ap.user_id = u.id
-- WHERE at.annotator_id = ap.id
--   AND u.email = '<email>'
--   AND at.status IN ('pending', 'in_progress', 'submitted');

-- UPDATE users_user u
-- SET is_active = true
-- FROM annotator_profile ap
-- WHERE ap.user_id = u.id
--   AND u.email = '<email>';

-- UPDATE annotator_profile ap
-- SET 
--     status = 'approved',
--     approved_at = NOW()
-- FROM users_user u
-- WHERE ap.user_id = u.id
--   AND u.email = '<email>';

-- Migration: Add annual_income column to users table
-- Run this in your Supabase SQL Editor

-- Add annual_income column to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS annual_income DECIMAL(15, 2) DEFAULT NULL;

-- Add comment to document the column
COMMENT ON COLUMN users.annual_income IS 'User annual income/salary for financial planning';

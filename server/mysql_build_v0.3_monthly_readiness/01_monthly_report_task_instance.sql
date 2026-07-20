CREATE TABLE IF NOT EXISTS monthly_report_task_instance (
  id BIGINT PRIMARY KEY,
  report_cycle_id BIGINT NOT NULL,
  upload_task_id VARCHAR(64) NULL,
  task_code VARCHAR(64) NOT NULL,
  task_name VARCHAR(255) NOT NULL,
  group_code VARCHAR(20) NOT NULL,
  task_mechanism VARCHAR(30) NOT NULL,
  scope_type VARCHAR(30) NOT NULL,
  scope_key VARCHAR(100) NOT NULL,
  monthly_status VARCHAR(30) NOT NULL,
  triggered_flag TINYINT NOT NULL DEFAULT 1,
  confirmation_required TINYINT NOT NULL DEFAULT 0,
  include_in_denominator TINYINT NOT NULL DEFAULT 0,
  responsible_unit VARCHAR(255) NOT NULL,
  deadline DATE NOT NULL,
  dedup_key VARCHAR(255) NOT NULL,
  validation_passed_at DATETIME NULL,
  not_applicable_reason VARCHAR(500) NULL,
  not_applicable_confirmed_by VARCHAR(100) NULL,
  not_applicable_confirmed_at DATETIME NULL,
  source_tag VARCHAR(50) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_monthly_task_cycle
    FOREIGN KEY (report_cycle_id) REFERENCES monthly_report_cycle(id),
  CONSTRAINT chk_monthly_task_status
    CHECK (monthly_status IN ('待提交', '待确认', '待补正', '校验通过', '不适用（已确认）')),
  CONSTRAINT chk_monthly_task_mechanism
    CHECK (task_mechanism IN ('MONTHLY_FIXED', 'CONDITIONAL', 'PERIODIC_REFERENCE')),
  CONSTRAINT chk_monthly_task_triggered
    CHECK (triggered_flag IN (0, 1)),
  CONSTRAINT chk_monthly_task_confirmation
    CHECK (confirmation_required IN (0, 1)),
  CONSTRAINT chk_monthly_task_denominator
    CHECK (include_in_denominator IN (0, 1)),
  UNIQUE KEY uk_monthly_task_dedup (report_cycle_id, dedup_key),
  INDEX idx_monthly_task_period_status (report_cycle_id, include_in_denominator, monthly_status),
  INDEX idx_monthly_task_code (task_code),
  INDEX idx_monthly_task_upload (upload_task_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月报资料任务实例统计扩展表';

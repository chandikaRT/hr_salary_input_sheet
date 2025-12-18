from odoo import models, fields, api

class PayrollInputSheet(models.Model):
    _name = 'hr.payroll.input.sheet'
    _description = 'Payroll Input Sheet'

    name = fields.Char('Description', compute='_compute_name')
    date = fields.Date(string='Date', required=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    line_ids = fields.One2many('hr.payroll.input.sheet.line', 'sheet_id', string='Lines')

    def _compute_name(self):
        for rec in self:
            rec.name = f"Payroll Inputs {rec.date.strftime('%B %Y')}"

    def action_apply_to_payslips(self):
        for line in self.line_ids:
            input_type = self.env['hr.salary.input'].search([('name', '=', line.input_name)], limit=1)
            if not input_type:
                input_type = self.env['hr.salary.input'].create({'name': line.input_name})
            payslips = self.env['hr.payslip'].search([
                ('employee_id', '=', line.employee_id.id),
                ('date_from', '>=', self.date.replace(day=1)),
                ('date_to', '<=', self.date.replace(day=1) + relativedelta(months=1, days=-1)),
            ])
            for slip in payslips:
                self.env['hr.payslip.input'].create({
                    'name': input_type.name,
                    'amount': line.amount,
                    'slip_id': slip.id,
                    'code': input_type.code,
                })

class PayrollInputSheetLine(models.Model):
    _name = 'hr.payroll.input.sheet.line'
    _description = 'Payroll Input Sheet Line'

    sheet_id = fields.Many2one('hr.payroll.input.sheet', string='Sheet')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    input_name = fields.Char('Input Name', required=True)
    amount = fields.Float('Amount', required=True)
    applied = fields.Boolean('Applied', default=False)
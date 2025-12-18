from odoo import models, fields, api
import base64
import xlrd
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class PayrollInputSheet(models.Model):
    _name = 'hr.payroll.input.sheet'
    _description = 'Payroll Input Sheet'

    name = fields.Char('Description', compute='_compute_name')
    date = fields.Date(string='Date', required=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    line_ids = fields.One2many('hr.payroll.input.sheet.line', 'sheet_id', string='Lines')
    file = fields.Binary('Excel File')
    filename = fields.Char('File Name')

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

    def action_import(self):
        self.ensure_one()
        if not self.file:
            raise ValidationError("No file uploaded.")
        data = base64.b64decode(self.file)
        try:
            workbook = xlrd.open_workbook(file_contents=data)
        except Exception as e:
            raise ValidationError("The uploaded file is not a valid Excel file.")
        sheet = workbook.sheet_by_index(0)

        lines = []
        for row in range(1, sheet.nrows):
            employee_code = sheet.cell(row, 0).value
            input_name = sheet.cell(row, 1).value
            amount = sheet.cell(row, 2).value

            employee = self.env['hr.employee'].search([('barcode', '=', employee_code)], limit=1)
            if employee:
                lines.append((0, 0, {
                    'employee_id': employee.id,
                    'input_name': input_name,
                    'amount': amount,
                }))
        self.line_ids = lines
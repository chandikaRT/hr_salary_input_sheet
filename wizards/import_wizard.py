from odoo import models, fields, api
import base64
import xlrd
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class ImportPayrollInputWizard(models.TransientModel):
    _name = 'hr.payroll.input.import.wizard'
    _description = 'Import Payroll Inputs from Excel'

    file = fields.Binary('Excel File', required=True)
    filename = fields.Char('File Name')
    date = fields.Date(string="Date", required=True)
    sheet_ref = fields.Many2one('hr.payroll.input.sheet', string='Payroll Input Sheet')

    def action_import(self):
        self.ensure_one()
        if not self.file:
            return
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

        payroll_sheet = self.env['hr.payroll.input.sheet'].create({
            'date': self.date,
            'line_ids': lines,
        })
        self.sheet_ref = payroll_sheet
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payroll Input Sheet',
            'res_model': 'hr.payroll.input.sheet',
            'view_mode': 'form',
            'res_id': payroll_sheet.id,
            'target': 'current',
        }
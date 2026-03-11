```python


from django.db import models

# Create your models here.
from django.utils.translation import gettext_lazy as _
from company.models import Company,Contact
from django.db.models import Sum
from django.utils import timezone
from django.urls import reverse
from addons.models import activearchlockedMixin, createdtimestamp_uid, addressMixin
from django.core.validators import int_list_validator
from django.db.models import Q
from djmoney.models.fields import MoneyField, CurrencyField
from contact.models import Phone,Address,Email,Website
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from djmoney.money import Money

from django.shortcuts import get_object_or_404

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
# from party.models import Staff, User


default_currency = 'GHS'  # Set your default currency here
allowed_currencies = ['GHS', 'USD', 'EUR', 'GBP','JPY']  # List of allowed currencies

class Charts_of_account(activearchlockedMixin, createdtimestamp_uid, models.Model):
    
    acc_number = models.PositiveIntegerField(_("Base Account Number"), editable=False,null=False,blank=False)
    name = models.CharField(_("Account Name"), max_length=50,null=False,blank=False,unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    TYPE_CHOICES = (
        ("Assets", "assets"),
        ("Expenses", "expenses"),
        ("Liabilities", "liabilities"),
        ("Revenues/Income", "revenues/income"),
        ("Capital/Equity", "capital/equity"),
    )

    account_type = models.CharField(
        _("Account Type"), max_length=20, choices=TYPE_CHOICES
    )
    account_balance_type = models.CharField(
        _("Balance type"),
        max_length=10,
        choices=(("Debit", "Debit"), ("Credit", "Credit")),
    )

    def save(self, *args, **kwargs):
        if self.account_type in ["Assets", "Expenses"]:
            self.account_balance_type = "Debit"
        elif self.account_type in ["Liabilities", "Revenues/Income", "Capital/Equity"]:
            self.account_balance_type = "Credit"
        else:
            raise Exception("Account type is not valid")

        if self._state.adding:
            # Determine the initial acc_number based on Accounttype
            if self.account_type == "Assets":
                last_acc_number = Charts_of_account.objects.filter(
                    account_type="Assets", 
                ).aggregate(models.Max("acc_number"))
                last_acc_number = last_acc_number["acc_number__max"]
                if last_acc_number:
                    self.acc_number = last_acc_number + 1000
                else:
                    self.acc_number = 10100000
            elif self.account_type == "Expenses":
                last_acc_number = Charts_of_account.objects.filter(
                    account_type="Expenses", 
                ).aggregate(models.Max("acc_number"))
                last_acc_number = last_acc_number["acc_number__max"]
                if last_acc_number:
                    self.acc_number = last_acc_number + 1000
                else:
                    self.acc_number = 20100000
            elif self.account_type == "Liabilities":
                last_acc_number = Charts_of_account.objects.filter(
                    account_type="Liabilities", 
                ).aggregate(models.Max("acc_number"))
                last_acc_number = last_acc_number["acc_number__max"]
                if last_acc_number:
                    self.acc_number = last_acc_number + 1000
                else:
                    self.acc_number = 30100000
            elif self.account_type == "Revenues/Income":
                last_acc_number = Charts_of_account.objects.filter(
                    account_type="Revenues/Income", 
                ).aggregate(models.Max("acc_number"))
                last_acc_number = last_acc_number["acc_number__max"]
                if last_acc_number:
                    self.acc_number = last_acc_number + 1000
                else:
                    self.acc_number = 40100000
            elif self.account_type == "Capital/Equity":
                last_acc_number = Charts_of_account.objects.filter(
                    account_type="Capital/Equity", 
                ).aggregate(models.Max("acc_number"))
                last_acc_number = last_acc_number["acc_number__max"]
                if last_acc_number:
                    self.acc_number = last_acc_number + 1000
                else:
                    self.acc_number = 50100000

        super(Charts_of_account, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Charts_of_account")
        verbose_name_plural = _("Charts_of_accounts")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Charts_of_account_detail", kwargs={"pk": self.pk})


# this work is for later
# Add a field (called 'accounts_id_reference' (editable=False,)) to the Account model that will store the id of the account 
# that is linked to the table that the account comes from/originates. 
# Edit the account name to allow it store the actual account name of the model form with name("Account Name") + "_" + "Account Type"
# Allow this feild to be editable on each model save.

class Account(createdtimestamp_uid, activearchlockedMixin, models.Model):
    
    # name = models.CharField(_("Name"), max_length=150,null=False,blank=False,)
    accounttype = models.ForeignKey(
        Charts_of_account, verbose_name=_("Account Type"), on_delete=models.DO_NOTHING,
        # related_name='account_type'
    )
    acc_number = models.PositiveIntegerField(
        _("Base Account Number"), editable=False, unique=True
    )
    # Allowed Models to be done later
    # ALLOWED_MODELS = []#list the accounting models
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    object_id = models.UUIDField()
    account_object = GenericForeignKey("content_type", "object_id")
    class Meta:
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")
        unique_together = ("object_id", "accounttype")

    def save(self, *args, **kwargs):
        if self._state.adding:
            acccount = Charts_of_account.objects.get(pk=self.accounttype.pk)
            acccountno = acccount.acc_number
            last_acc_nu = Account.objects.filter(
                accounttype=self.accounttype
            ).aggregate(largest=models.Count("accounttype"))["largest"]
            self.acc_number = last_acc_nu + 1 + acccountno
        super(Account, self).save(*args, **kwargs)  # Call the real save() method

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        return reverse("Account_detail", kwargs={"pk": self.pk})
    
    def clean_allowed_models(self):
        if self.content_type.model not in self.ALLOWED_MODELS:
            raise ValidationError(f"Invalid preference type: {self.content_type.model}")
        pass
    
    @property
    def running_balance(self):
        debit_sum = (
            Transaction.objects.filter(account=self, transaction_type="Debit")
            .aggregate(total=Sum("amount_default"))
            .get("total", 0)
        )
        credit_sum = (
            Transaction.objects.filter(account=self, transaction_type="Credit")
            .aggregate(total=Sum("amount_default"))
            .get("total", 0)
        )
        debit_sum = debit_sum if debit_sum is not None else 0
        credit_sum = credit_sum if credit_sum is not None else 0

        if self.accounttype.account_balance_type == "Debit":
            balance = debit_sum - credit_sum
        else:
            balance = credit_sum - debit_sum

        return balance
    def clean(self):
        # self.clean_allowed_models()
        return super().clean()
    

class TransactionDoc(createdtimestamp_uid):
    
    datetimestamp = models.DateTimeField(
        _("Date Time"), auto_now=True, auto_now_add=False
    )
    description = models.TextField(_("Description"))

    ALLOWED_MODELS = []
    #list the models that affect the accounting model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    transaction_object = GenericForeignKey("content_type", "object_id")

    # user = models.ForeignKey(
    #     User, verbose_name=_("User"), on_delete=models.CASCADE
    # )
    def clean_allowed_models(self):
        if self.content_type.model not in self.ALLOWED_MODELS:
            raise ValidationError(f"Invalid Transaction Doc: {self.content_type.model}")
        pass
    def clean(self):
        self.clean_allowed_models()
        return super().clean()

    class Meta:
        verbose_name = _("TransactionDoc")
        verbose_name_plural = _("TransactionDocs")

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return reverse("TransactionDoc_detail", kwargs={"pk": self.pk})

# @receiver(post_save, sender=itemvariant)
# def create_financialtransaction_instance(sender, instance, created, **kwargs):
    
#     if created:
#         preference.objects.create(
#             content_type=ContentType.objects.get_for_model(sender),
#             object_id=instance.id,
#             # 
#         )



###the purpose of this is to track the change of ownership and transactions and sales cash, 
# and related inventory movements
class Transaction(createdtimestamp_uid, models.Model):
    notes=models.ForeignKey(TransactionDoc, verbose_name=_("Notes"), on_delete=models.CASCADE,related_name='transactions')
    amount = MoneyField(
        decimal_places=2, default=0,  max_digits=20,
        default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies],
    )
    account = models.ForeignKey(
        Account,
        verbose_name=_("Account"),
        on_delete=models.CASCADE,
        related_name='account_transactions'
    )
    COA = models.ForeignKey(
        Charts_of_account, verbose_name=_("Chart of Account"), on_delete=models.CASCADE,
        related_name='chart_of_account_transactions',

        )
    transaction_type = models.CharField(
        _("Transaction Type"),
        max_length=10,
        choices=(("Debit", "Debit"), ("Credit", "Credit")),
    )
    conversion_rate = models.DecimalField(
        _("Rate"),
        max_digits=10,
        decimal_places=4,
        default=1,
    )
    amount_default=MoneyField(
        _("Amount Default"), max_digits=20, decimal_places=2, default=0,
        default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies],
    )

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")

    """    
    select sum(case when direction == 1 then amount end) as DR,
            sum(case when direction == -1 then amount end) as CR
            from
            transactions;
    """

    def average_amount(self):
        return Transaction.objects.aggregate(average_amount=models.Avg("amount_default"))[
            "average_amount"
        ]

    def Verifydebitcredit(self):
        debits = Transaction.objects.filter(transaction_type="Debit").aggregate(
            Sum("amount_default")
        )["amount_default__sum"]
        credits = Transaction.objects.filter(transaction_type="Credit").aggregate(
            Sum("amount_default")
        )["amount_default__sum"]
        if debits == credits:
            return True
        # else:
        raise Exception("Debits and Credits are not equal")

    def checkdebitcredit(self):
        debits = Transaction.objects.filter(transaction_type="Debit").aggregate(
            Sum("amount_default")
        )["amount_default__sum"]
        credits = Transaction.objects.filter(transaction_type="Credit").aggregate(
            Sum("amount_default")
        )["amount_default__sum"]
        sum = debits - credits
        if sum == 0:
            return True
        else:
            return sum

    def __str__(self):
        return f"{self.account.acc_number} {self.amount}  {self.transaction_type}"

    def get_absolute_url(self):
        return reverse("transaction_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        # self.COA = self.account.accounttype
        if self.account:
            self.COA = self.account.accounttype
        else:
            raise Exception("Account is required")
        self.amount_default = self.amount / self.conversion_rate
        super(Transaction, self).save(*args, **kwargs)



# add a model to track transaction costs for payment of goods and services
class paymentbase(models.Model):
    # this is limited to payment between the company cash account and the expense accounts
    # this is ideal for paying a supplier or even paying staff or any kind of payment
    paymentmethodchoices = (
        ("cash", "cash"),
        ("cheque", "cheque"),
        # ("creditcard", "creditcard"),
        # ("debitcard", "debitcard"),
        ("banktransfer", "banktransfer"),
        ("mobilemoney", "mobilemoney"),
        # ('paypal','paypal') ,
        # ('stripe','stripe') ,
    )  
    paymentmethod=models.CharField(_("Payment Method"), max_length=50, choices=paymentmethodchoices)
    reference=models.CharField(_("Reference"), max_length=250)
    paymentnotes=models.TextField(_("Payment Notes"), blank=True, null=True)
    Transaction=models.ForeignKey(TransactionDoc, verbose_name=_("Transaction"), on_delete=models.CASCADE)
    amount=models.DecimalField(_("Amount"), max_digits=15, decimal_places=2)
    paymentdate=models.DateTimeField(_("Payment Date"), auto_now=False, auto_now_add=False)

    
    class Meta:
        abstract = True

    # link each type of transaction to a payment method model with a foreign key
    # this will allow us to track the payment method used for each transaction
    # and also to track the payment method used for each transaction
    # and also allow you see the payment method details regarding the payment method in question


# create a model for handling payment requests and payment confirmations with payment sources
# this payment module will have a status field to track the status of the payment request
# class PaymentRequest(paymentbase):
#     class Meta:
#         verbose_name = _("PaymentRequest")
#         verbose_name_plural = _("PaymentRequests")
        

class Bank(createdtimestamp_uid, models.Model):
    name = models.CharField(_("Bank Name"), max_length=50,unique=True)
    ismainbranch = models.BooleanField(_("Main Branch"), default=False)
    location = models.ForeignKey(
        Address, verbose_name=_("Location Address"), on_delete=models.PROTECT
    )
    branchof = models.ForeignKey(
        "self", verbose_name=_("Is a branch of"), on_delete=models.CASCADE,blank=True, null=True
    )
    
    contact=models.ManyToManyField(Contact, verbose_name=_("Contact"),blank=True)
    notes_account = models.ForeignKey(
        Account,
        editable=False,
        verbose_name=_("Notes Payable Account"),
        on_delete=models.CASCADE,
        limit_choices_to=Q(accounttype__name="Notes Payable"),
        related_name="banknotespayable",
        null=True,
        blank=True
    )
    # notes account is for when the business goes for a loan and notes insterest account is for when the business has to pay a certain interest on loan based on a structured design
    notes_interest_account = models.ForeignKey(
        Account,
        editable=False,
        verbose_name=_("Interest"),
        on_delete=models.CASCADE,
        limit_choices_to=Q(accounttype__name="Interest Payable"),
        related_name="banknotesinterest",
        null=True,
        blank=True
    )
    
    def save(self, *args, **kwargs):
        # if self._state.adding:
            # notesaccount=Charts_of_account.objects.get(
            #     name="Notes Payable",
            #     ,
            # ) 
            # notesaccount=Account.objects.create(
            #     name= self.name,
            #     accounttype=notesaccount,
            # )
            
            # self.notes_account =notesaccount
            # notesinterestcharts=Charts_of_account.objects.get(
            #     name="Interest Payable",
            #     ,
            #     )
            # notesinterestaccount=Account.objects.create(
            #     name=self.name,
            #     accounttype=notesinterestcharts
            #     )
            # self.notes_interest_account=notesinterestaccount
            # pass
        super(Bank, self).save(*args, **kwargs) # Call the real save() method

    class Meta:
        verbose_name = _("Bank")
        verbose_name_plural = _("Banks")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Bank_detail", kwargs={"pk": self.pk})


class BankAccount(createdtimestamp_uid, activearchlockedMixin, models.Model):

    bank = models.ForeignKey(Bank, verbose_name=_("Bank"), on_delete=models.CASCADE)
    name=models.CharField(_("Bank Account Name"), max_length=50)
    cash_account = models.ForeignKey(
        Account,
        verbose_name=_("Cash Account Type"),
        on_delete=models.CASCADE,
        limit_choices_to=Q(accounttype__name="Current Asset"),
        null=True,
        blank=True,
        editable=False
    )
    accounttype = (("savings", "savings"), ("checking", "checking"))
    # company = models.ForeignKey(
    #     Company, verbose_name=_("Company"), on_delete=models.CASCADE
    # )
    account_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        validators=[int_list_validator(sep="", message=_("Only digits allowed"))],
        verbose_name=_("Account Number"),
    )
    routing_number = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        validators=[int_list_validator(sep="", message=_("Only digits allowed"))],
        verbose_name=_("Routing Number"),
    )
    swift_number = models.CharField(
        max_length=30, null=True, blank=True, verbose_name=_("SWIFT Number")
    )
    account_type = models.CharField(
        choices=accounttype,
        max_length=10,
        default="checking",
        verbose_name=_("Account Type"),
    )

    class Meta:
        verbose_name = _("BankAccount")
        verbose_name_plural = _("BankAccounts")
        unique_together=('bank','account_number')

    def save(self, *args, **kwargs):
    #    if self._state.adding:
        super(BankAccount, self).save(*args, **kwargs) # Call the real save() method
    
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("BankAccount_detail", kwargs={"pk": self.pk})




class Tax(createdtimestamp_uid, activearchlockedMixin, models.Model):
    
    name = models.CharField(_("Tax Name"), max_length=50,unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    effectivedate = models.DateField(
        _("Effective date"), auto_now=False, auto_now_add=False
    )
    is_tax_recoverable = models.BooleanField(_("Is Tax Recoverable"), default=False)
    tax_payable_account = models.ForeignKey(
        Account,
        editable=False,
        verbose_name=_("Financial Ledger Account"),
        on_delete=models.CASCADE,
        limit_choices_to=Q(accounttype__name="Taxes Payable"),
        null=True,
        blank=True,
        related_name="tax_payable_account"
    )
    tax_expense_account = models.ForeignKey(
        Account,
        editable=False,
        verbose_name=_("Financial Ledger Account"),
        on_delete=models.CASCADE,
        limit_choices_to=Q(accounttype__name="Tax Expense"),
        null=True,
        blank=True,
        related_name="tax_expense_account"
    )
    taxcounttype=(('percent','percent'),('amount','amount'))
    tax_type=models.CharField(_("Tax Type"), max_length=50, choices=taxcounttype,default='percent')
    maxtaxable_amount = models.DecimalField(
        _("Maximum Taxable amount"),
        help_text=_(
            "The monetary value of the tax for which transactions above is tax free. Example: taxing a 1200 at a 10% rate with 100 tax max limit means only the 100 is taxed and the rest  1100 is tax free. When set to 0 or null or blank, does not apply always applies."
        ),
        max_digits=18,
        decimal_places=2,
        default=0,
    )
    mintaxable_amount = models.DecimalField(
        _("Minimum Taxable amount"),
        help_text=_(
            "The monetary value of the transaction for which tax can be calculated. This means only transactions above this amount are taxable. When set to 0 or null or blank, does not apply always applies."
        ),
        max_digits=18,
        decimal_places=2,
        default=0,
    )
    tax = models.DecimalField(
        _("Tax"), max_digits=18, decimal_places=4, default=0
    )
    class Meta:
        verbose_name = _("Tax")
        verbose_name_plural = _("Taxes")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Tax_detail", kwargs={"pk": self.pk})
    
    def cleanex(self):
        
        if self.tax_type == "percent" and not (0 <= self.tax <= 100):
            raise ValidationError(
                {"discount": _("For tax percentage discounts, the value must be between 0 and 100.")}
            )
        elif self.tax_type == "amount" and self.tax < 0:
            raise ValidationError(
                {"discount": _("For tax amount discounts, the value must be non-negative.")}
            )
        # ensure that if both mintaxable_amount and maxtaxable_amount are set, then they must be valid
        if self.mintaxable_amount and self.mintaxable_amount > 0 and self.maxtaxable_amount and self.maxtaxable_amount > 0 and self.mintaxable_amount > self.maxtaxable_amount:
            raise ValidationError(
                {"mintaxable_amount": _("Minimum taxable amount must be less than maximum taxable amount.")}
            )
        pass

    def clean(self):
        self.cleanex()
        return super().clean()
    
    def save(self, *args, **kwargs):
            
        super(Tax, self).save(*args, **kwargs) # Call the real save() method


# function to calculate a tax amount based on an amount provided and tax id
def calculate_tax_amount(amount, tax_id):
    taxableamount = Money(0, 'GHS')
    if not isinstance(amount, Money):
        raise TypeError("Amount must be a Money instance")
    amount = Money(amount.amount, 'GHS')
    tax = get_object_or_404(Tax, pk=tax_id)
    if tax.mintaxable_amount > amount.amount and tax.mintaxable_amount > 0:
        return taxableamount, tax
    if tax.maxtaxable_amount < amount.amount and tax.maxtaxable_amount > 0:
        taxableamount = Money(tax.maxtaxable_amount, 'GHS')
    else:
        taxableamount = Money(amount.amount,'GHS')
    if tax.tax_type == "percent":
        taxableamount = taxableamount * tax.tax
        return taxableamount,tax
    elif tax.tax_type == "amount":
        taxableamount = Money(tax.tax, 'GHS')
        return taxableamount,tax
    return Money(0, 'GHS'), tax




from department.models import Branch,Department
from sales.models import Tender_Repository
from party.models import Staff,Client,Vendor
from invplan.models import Carrier
from hrm.models import Deduction,Employee_Deduction
# from hrm.models import 

# campaign have a schedule of activities and tasks

class BudgetType(createdtimestamp_uid):
    # budget types are used to classify budgets for different purposes 
    # and includes the approving managers for each type of budget
    # budget types are linked to departments
    # examples of budget types are marketing budget, sales budget, operational budget, project budget, etc
    name = models.CharField(max_length=255,)
    description = models.TextField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, verbose_name=_("Department"))
    assigned_approving_manager = models.ManyToManyField(Staff, verbose_name=_("Approving Manager"), related_name="budget_types",)
    class Meta:
        verbose_name = _("Budget Type")
        verbose_name_plural = _("Budget Types")
        unique_together = ("name", "department")


    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("BudgetType_detail", kwargs={"pk": self.pk})


class BudgetRequest(createdtimestamp_uid):
    # holds the source of the budget request and the direct model or entity to benefit
    # 
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    source_object = GenericForeignKey("content_type", "object_id")
    
    # campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, verbose_name=_("Campaign"), related_name="budget_requests")
    # budget_request_source
    # budget_request_type
    amount = MoneyField(
        _("Amount"),
        max_digits=20,
        decimal_places=2,
        default=0,
        # default_currency='GHS'
        default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies],

    )
    budget_type = models.ForeignKey(BudgetType, on_delete=models.PROTECT, verbose_name=_("Budget Type"),)
    reason = models.TextField()
    requested_by = models.ForeignKey(Staff, on_delete=models.PROTECT, verbose_name=_("Requested By"), related_name="budget_requests",)
    date_requested = models.DateField(auto_now_add=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('pending', 'Pending'),
        ('needs_revision', 'Needs Revision'),
        ('cancelled', 'Cancelled'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    approving_staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, verbose_name=_("Approving Staff"), related_name="approving_budget_requests", null=True, blank=True)
    # defaults to the manager of the department of the budget type
    date_approved = models.DateTimeField(blank=True, null=True)
    # if approved then a budget expense request is created and when approved the budget is allocated
    # this will cause a financial transaction to be created in the accounts module meaning the budget has been allocated

    class Meta:
        verbose_name = _("Budget Request")
        verbose_name_plural = _("Budget Requests")

    def __str__(self):
        return f"Budget Request: {self.amount} for Campaign: {self.campaign.name}"

    def get_absolute_url(self):
        return reverse("BudgetRequest_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        # raise an error if approving staff is not same as budget type approving manager when status is approved
        if self.status == 'approved' and self.approving_staff != self.budget_type.approving_manager:
            raise ValidationError(_("Approving staff must be the approving manager of the budget type when status is approved."))
        if self.status == 'approved' and self.date_approved is None:
            self.date_approved = timezone.now()
        
        super(BudgetRequest, self).save(*args, **kwargs) # Call the real save() method


class BudgetAllocation(createdtimestamp_uid):
    # this hold the beneficiary of the budget allocation
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # object_id = models.UUIDField()
    # source_object = GenericForeignKey("content_type", "object_id")
    # 
    # budget_request_source
    # budget_request_type
    transaction = models.ForeignKey(TransactionDoc, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Transaction"))
    amount = MoneyField(
        _("Amount"),
        max_digits=20,
        decimal_places=2,
        default=0,
        default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies],
        # default_currency='GHS'
    )
    budget_request = models.ForeignKey(BudgetRequest, on_delete=models.PROTECT, verbose_name=_("Budget Request"))
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('allocated', 'Allocated'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    description = models.TextField(blank=True, null=True)
    allocated_to = models.ForeignKey(Staff, on_delete=models.PROTECT, verbose_name=_("Allocated To"), related_name="allocated_budgets_to", )
    allocated_by = models.ForeignKey(Staff, on_delete=models.PROTECT, verbose_name=_("Allocated By"), related_name="allocated_budgets_by", )
    

    class Meta:
        verbose_name = _("Budget Allocation")
        verbose_name_plural = _("Budget Allocations")

    def __str__(self):
        return f"Budget Allocation: {self.amount} for: {self.allocated_to}"

    def get_absolute_url(self):
        return reverse("BudgetAllocation_detail", kwargs={"pk": self.pk})


class ExpenseType(createdtimestamp_uid):
    name = models.CharField(max_length=255,unique=True,)
    description = models.TextField(blank=True, null=True)
    # ewpense_report_type_choices = (
    #     ('travel', 'Travel'),
    #     ('meals', 'Meals'),
    #     ('accommodation', 'Accommodation'), 
    #     ('supplies', 'Supplies'),
    #     ('other', 'Other'),
    # )
    department= models.ForeignKey(Department, on_delete=models.PROTECT, verbose_name=_("Department"))
    class Meta:
        verbose_name = _("Expense Type")
        verbose_name_plural = _("Expense Types")
        unique_together = ("name",)


    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("ExpenseType_detail", kwargs={"pk": self.pk})    



# expense reports can be added later
class ExpenseReport(createdtimestamp_uid):
    # shows the budget from which the expense is being reported
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.PROTECT, verbose_name=_("Expense Type"))
    budget_allocation = models.ForeignKey(BudgetAllocation, on_delete=models.PROTECT, verbose_name=_("Budget"), limit_choices_to=Q(status='allocated'),)
    amount = MoneyField(
        _("Amount"),
        max_digits=20,
        decimal_places=2,
        default=0,
        default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies],
    )
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('draft', 'Draft'),
        ('completed', 'Completed'),
        ('locked', 'Locked'),
    ], default='draft')
    # this is used to track the utilized amount from the budget
    returned_amount = MoneyField(
        _("Returned Amount"),
        max_digits=20,
        decimal_places=2,
        default=0,
        default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies],
        
        # default_currency='GHS'
    )
    transaction = models.ForeignKey(TransactionDoc, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Transaction"))
    
    description = models.TextField(blank=True, null=True)
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, verbose_name=_("Reported By"), related_name="expense_reports",)
    incurred_on = models.DateTimeField(auto_now=False, auto_now_add=False, verbose_name=_("Incurred On"),)

    class Meta:
        verbose_name = _("Expense Report")
        verbose_name_plural = _("Expense Reports")
    
    # def 
    # prevent the expense report from getting changed if status is completed =>

    def __str__(self):
        return f"Expense Report: {self.amount} for Allocated Budget: {self.budget_allocation.__str__()}"

    def get_absolute_url(self):
        return reverse("ExpenseReport_detail", kwargs={"pk": self.pk})





class TransactionRequestType(createdtimestamp_uid):
    # example types: purchase order, sales order, expense request, payment request, refund request
    transaction_type=(
        ('Expense','Expense'),
        ('Revenue','Revenue'),
        ('Transfer','Transfer'),
        ('Adjustment','Adjustment'),
        ('Payroll','Payroll'),
        ('Credit Note','Credit Note'),
        ('Debit Note','Debit Note'),
        ('Loan','Loan'),
        ('Investment','Investment'),
    # ()
    )
    name = models.CharField(_("Transaction Request Type Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)

    class Meta:
        verbose_name = _("Transaction Request Type")
        verbose_name_plural = _("Transaction Request Types")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("TransactionRequestType_detail", kwargs={"pk": self.pk})

class TransactionRequest(createdtimestamp_uid):
# Debits record value entering an account, credits record value leaving or increasing liabilities, equity, and revenue. Use the DEALER mnemonic. Dividends, Expenses, Assets are debit‑normal, Liabilities, Equity, Revenue are credit‑normal.
    transaction_type = models.ForeignKey(
        TransactionRequestType, verbose_name=_("Transaction Request Type"), on_delete=models.PROTECT,
    )
    # this model will be used to track the transaction requests and their approval process before they are converted to actual transactions in the system. This is ideal for tracking purchase orders, sales orders, expense requests, payment requests, etc. This will also allow us to have a clear audit trail of all transaction requests and their approval process.
    # this model has two accounts. One cash account and one expense account. The cash account is the account that will be used to pay for the transaction and the expense account is the account that will be used to record the expense of the transaction. This is ideal for tracking purchase orders, sales orders, expense requests, payment requests, etc. This will also allow us to have a clear audit trail of all transaction requests and their approval process.
    # the cash account will always correspond to the debit account and the expense account will always correspond to the credit account. This is ideal for tracking purchase orders, sales orders, expense requests, payment requests, etc. This will also allow us to have a clear audit trail of all transaction requests and their approval process.
    transaction_direction_choices = (
        ("debit", "Debit"),
        ("credit", "Credit"),
    )
    increase_direction = models.CharField(
        _("Increase Direction"), max_length=10, choices=transaction_direction_choices,
    )
    statuschoices = (
        ("pending", "pending"),
        ("approved", "approved"),
        ("rejected", "rejected"),
    )
    status = models.CharField(
        _("Status"), max_length=10, choices=statuschoices, default="pending"
    )
    description = models.TextField(_("Description"),)
    transactiondoc = models.ForeignKey(TransactionDoc, verbose_name=_("Transaction"), on_delete=models.CASCADE,null=True, blank=True)
    amount = MoneyField(_("Transaction Amount"),
        decimal_places=2, default=0, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies],
         max_digits=20
    )
    approving_staff = models.ForeignKey(
        Staff, verbose_name=_("Approving Staff"), on_delete=models.PROTECT, related_name="trans_approving_staff",
    )    
    debit_account = models.ForeignKey(
        Account,
        verbose_name=_("Debit Account"),
        on_delete=models.CASCADE,
        related_name='debit_request_account', 
        # limit_choices_to=(Q(accounttype__account_balance_type="Debit") & Q(accounttype__account_type__in=["Operational Income","Revenue/Income","Capital"]) )| (Q(accounttype__account_balance_type="Credit") & Q(accounttype__account_type__in=["Regular Expense","Depreciation Expense","Marketing Expenses","Inventory","Accounts Payable","Wages Payable","Tips Payable"])),
    )
    credit_account = models.ForeignKey(
        Account,
        verbose_name=_("Credit Account"),
        on_delete=models.CASCADE,
        related_name='credit_request_account', 
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    source_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("Transaction Request")
        verbose_name_plural = _("Transaction Requests")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("TransactionRequest_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        # every single transaction request must have a transaction doc created for it
        # if not self.transactiondoc:
        super(TransactionRequest, self).save(*args, **kwargs) # Call the real save() method


@receiver(post_save, sender=Tax)
@receiver(post_save, sender=Bank)
@receiver(post_save, sender=BankAccount)
@receiver(post_save, sender=Branch)
@receiver(post_save, sender=Staff)
@receiver(post_save, sender=Tender_Repository)
@receiver(post_save, sender=Client)
@receiver(post_save, sender=Vendor)
@receiver(post_save, sender=Carrier)
@receiver(post_save, sender=Employee_Deduction)
def create_account_instance(sender, instance, created, **kwargs):
    id_val= resolveid(instance)
    # print(instance.pk)
    # print(id_val)
    # print(instance)
    # print(id_val)
    print(ContentType.objects.get_for_model(sender).name)
    instances={
        'Bank':['Notes Payable','Interest Payable'],
        'BankAccount':'Current Asset',
        'Tax':'Taxes Payable',
        'Branch':["Inventory","Accounts Payable","Wages Payable","Capital","Revenue/Income","Operational Income",
                  "Regular Expense","Depreciation Expense","Marketing Expenses",],
        'Staff':'Payroll Expenses',
        'Tender_Repository':'Cash',
        'Client':'Accounts Receivables',
    }
    # for x, y in instances.items():
    #     # Consider using this to create a preference instance for each type of model... However, it's not clear how to handle the case where a model is created and then deleted.
    #     print(x, y)

    if created:
        try:
            if ContentType.objects.get_for_model(sender).name == 'Bank':
                notesaccount=Charts_of_account.objects.get(
                    name="Notes Payable",
                    ) 
                notesaccount=Account.objects.create(
                    content_type=ContentType.objects.get_for_model(sender),
                    object_id=id_val,
                    accounttype=notesaccount,
                )
                
                # instance.notes_account =notesaccount
                notesinterestcharts=Charts_of_account.objects.get(
                    name="Interest Payable",
                    )
                notesinterestaccount=Account.objects.create(
                    content_type=ContentType.objects.get_for_model(sender),
                    object_id=id_val,
                    accounttype=notesinterestcharts
                    )
                # instance.notes_interest_account=notesinterestaccount
                Bank.objects.filter(pk=id_val).update(notes_interest_account=notesinterestaccount,notes_account =notesaccount)

            elif ContentType.objects.get_for_model(sender).name == 'BankAccount':
                curraccount=Charts_of_account.objects.get(
                    name="Current Asset",
                ) 
                currentass=Account.objects.create(
                    content_type=ContentType.objects.get_for_model(sender),
                    object_id=id_val,
                    accounttype=curraccount,
                )
                BankAccount.objects.filter(pk=id_val).update(notes_account =currentass)

    

            elif ContentType.objects.get_for_model(sender).name == 'Tax':

                TAXPAYaccount, created = Charts_of_account.objects.get_or_create(
                    name="Taxes Payable",
                ) 
                TAXass, created = Account.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(sender),
                    object_id=id_val,
                    accounttype=TAXPAYaccount,
                )
                
                TAXEXPaccount=Charts_of_account.objects.get(
                    name="Tax Expense",
                )
                TAXEXPass, created = Account.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(sender),
                    object_id=id_val,
                    accounttype=TAXEXPaccount,
                ) 

                Tax.objects.filter(id=id_val).update(tax_expense_account=TAXEXPass,tax_payable_account=TAXass)
                # carrier=Carrier.objects.filter(pk=id_val).update(carrieraccount=account)
                # tax.tax_expense_account=TAXEXPass
                # tax.tax_payable_account=TAXass
                


            elif ContentType.objects.get_for_model(sender).name == 'Branch':
                assets=[
                    "Inventory",
                    'Accounts Receivables',
                    "Cash",
                ]
                liabilities=[
                    "Accounts Payable",
                    "Wages Payable",
                    'Tips Payable',
                ]
                equity=[
                    "Capital",
                ]
                revenue=[
                    "Revenue/Income",
                    "Operational Income",
                ]
                expenses=[
                    "Regular Expense",
                    "Depreciation Expense",
                    "Marketing Expenses",
                    'Freight Expense',
                    "Cost of Goods Sold",
                ]
                # bbr=[
                #     Charts_of_account.objects.get_or_create(name=ex,account_type="Expenses",account_balance_type="Debit")
                #     for ex in expenses
                # ]
                # bbr=[
                #     Charts_of_account.objects.get_or_create(name=r,account_type="Revenues/Income",account_balance_type="Credit")
                #     for r in revenue
                # ]     
                # bbr=[
                #     Charts_of_account.objects.get_or_create(name=l,account_type="Liabilities",account_balance_type="Credit")
                #     for l in liabilities
                # ]
                # bbr=[
                #     Charts_of_account.objects.get_or_create(name=e,account_type="Capital/Equity",account_balance_type="Credit")
                #     for e in equity           
                # ]

                branchassets=[
                    Charts_of_account.objects.get(name=a,account_type="Assets",account_balance_type="Debit")
                    for a in assets
                    ]
                # print(branchassets)
                branchliabilities=[
                    Charts_of_account.objects.get(name=l,account_type="Liabilities",account_balance_type="Credit")
                    for l in liabilities
                ]
                branchequity=[
                    Charts_of_account.objects.get(name=e,account_type="Capital/Equity",account_balance_type="Credit")
                    for e in equity
                ]
                branchrevenue=[
                    Charts_of_account.objects.get(name=r,account_type="Revenues/Income",account_balance_type="Credit")
                    for r in revenue
                ]
                branchexpenses=[
                    Charts_of_account.objects.get(name=ex,account_type="Expenses",account_balance_type="Debit")
                    for ex in expenses
                ]
                accountspec=branchassets+branchliabilities+branchequity+branchrevenue+branchexpenses
                accountslist=[]
                for acc in accountspec:
                    account, created = Account.objects.get_or_create(
                        content_type=ContentType.objects.get_for_model(sender),
                        object_id=id_val,
                        accounttype=acc,
                    )
                    accountslist.append(account)
                branch=Branch.objects.get(pk=id_val)
                branch.branchaccount.set(accountslist)

            elif ContentType.objects.get_for_model(sender).name == 'staff':
                accounttype = Charts_of_account.objects.get(
                    name="Payroll Expenses", 
                )
                
                staffacco,created = Account.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(sender),
                    object_id=id_val,
                    accounttype=accounttype,
                )

                Staff.objects.filter(pk=id_val).update(staffaccount=staffacco)
                accounttype = Charts_of_account.objects.get( 
                    name="Accounts Receivables", 
                )
                
                credit_staffacco, created = Account.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(sender),
                    object_id=id_val,
                    accounttype=accounttype,
                )
                Staff.objects.filter(pk=id_val).update(credit_sale_account=credit_staffacco)
            elif ContentType.objects.get_for_model(sender).name == 'Tender Repository':
                print(ContentType.objects.get_for_model(sender).name)
                coa = Charts_of_account.objects.get(name="Cash")
                
                acc,creat = Account.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(sender),
                    object_id=id_val,
                    accounttype=coa
                    )
                Tender_Repository.objects.get(pk=id_val).branch.branchaccount.add(acc)
                Tender_Repository.objects.filter(pk=id_val).update(account=acc)

            elif ContentType.objects.get_for_model(sender).name == 'Client':

                accounttype = Charts_of_account.objects.get(
                    name="Accounts Receivables", 
                )
                custacco = Account.objects.create(
                    content_type=ContentType.objects.get_for_model(sender),
                    object_id=id_val,
                    accounttype=accounttype,
                )
                Client.objects.filter(pk=id_val).update(Clientaccount = custacco)

            elif ContentType.objects.get_for_model(sender).name == 'Vendor':
                accounttype = Charts_of_account.objects.get(
                    name="Accounts Payable", 
                )
                print('here')
                print(id_val)
                custacco = Account.objects.create(
                    content_type=ContentType.objects.get_for_model(sender),
                    object_id=id_val,
                    accounttype=accounttype,
                )
                Vendor.objects.filter(pk=id_val).update(vendoraccount = custacco)

     

            elif ContentType.objects.get_for_model(sender).name == 'Carrier':
                accounttype= Charts_of_account.objects.get(
                    name="Accounts Payable",
                )
                account,created=Account.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(sender),
                    object_id=id_val,
                    accounttype=accounttype,
                )
                print(account)
                carrier=Carrier.objects.filter(pk=id_val).update(carrieraccount=account)

            elif ContentType.objects.get_for_model(sender).name == 'Employee_Deduction':
                accounttype= Charts_of_account.objects.get(
                    name="Other Liabilities",
                )
                account,created=Account.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(sender),
                    object_id=id_val,
                    accounttype=accounttype,
                )
                print(account)
                deduction=Employee_Deduction.objects.filter(pk=id_val).update(account=account)
            else:
                pass
            
            # raise ValueError("Debugging create_account_instance")

        except Exception as e:
            print(f"Error creating account instance for {sender.__name__}: {e}")
            raise ValidationError(
                _(f"The Charts of Account for this model does not exist. Please create it first. {sender.__name__} ")
            )


def resolve_company(instance):
    for attr_chain in [
        ['company'],
        ['bank', 'company'],
        ['staff', 'company'],
        ['Clientdepartment', 'company'],
        ['department', 'company'],
        ['branch', 'department', 'company']
    ]:
        current = instance
        for attr in attr_chain:
            current = getattr(current, attr, None)
            if current is None:
                break
        if current:
            return current
    return None

def resolveid(instance):
    for attr_chain in [
        ['id'],
        ['pk'],
        ['staff', 'id'],
    ]:
        
        current = instance
        for attr in attr_chain:
            current = getattr(current, attr, None)
            if current is None:
                break
        if current:
            return current
    if hasattr(instance, 'pk'):
        return instance.pk
    elif hasattr(instance, 'id'):
        return instance.id
    elif hasattr(instance, 'staff'):
        if instance.staff.pk:
            return instance.staff.pk
        else:
            return instance.staff.id
    return None

```


```python

from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.db import models
from addons.models import (
    createdtimestamp_uid,
    CompanyMixin,
    createtimstam_uid
)
from django.core.validators import RegexValidator
from contact.models import Phone,Address,Email,Website
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from djmoney.models.fields import CurrencyField

# create a vault app for handling sensitive data
# such as payment methods, api keys, etc. 



class Industry(createtimstam_uid):
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    additional_info = models.JSONField(blank=True, null=True, default=dict)
    
    class Meta:
        verbose_name = _("Industry")
        verbose_name_plural = _("Industries")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Industry_detail", kwargs={"pk": self.pk})

class PaymentClass(models.Model):
    name = models.CharField(_("Payment Class"), max_length=50)
    #  to be linked with a payment method and validation
    #  this will check payment status and limit use
    class Meta:
        verbose_name = _("PaymentClass")
        verbose_name_plural = _("PaymentClasss")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("PaymentClass_detail", kwargs={"pk": self.pk})


class Contact(createtimstam_uid):
    ALLOWED_MODELS = ['Phone','Address','Website','Email',]
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, editable=False)
    
    contact_id = models.UUIDField(editable=False )
    is_verified=models.BooleanField(_("Is Verified"), default=False)
    contactobject = GenericForeignKey("content_type", "contact_id")
    related_contacts=models.ManyToManyField("self", blank=True, verbose_name=_("Related Contacts"))
    class Meta:
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")
    
    def __str__(self):
        return f"{self.content_type.model}: {self.contactobject}"

    def get_absolute_url(self):
        return reverse("contact_detail", kwargs={"pk": self.pk})
    
    def clean(self):
        self.cleanex()
        return super().clean()

    def cleanex(self):
        if self.content_type.model not in self.ALLOWED_MODELS:
            raise ValidationError(f"Invalid preference type: {self.content_type.model}")
        pass
    

@receiver(post_save, sender=Phone)
@receiver(post_save, sender=Address)
@receiver(post_save, sender=Website)
@receiver(post_save, sender=Email)
def create_contact_instance(sender, instance, created, **kwargs):
    if created:
        Contact.objects.create(
            content_type=ContentType.objects.get_for_model(sender),
            contact_id=instance.id,
        )


from contact.models import Country
# Create your models here.

class BusinessType(createtimstam_uid):
    # to be changed and use

    
    # servicetypes=(
    #     ('Pharmacy','Pharmacy'),
    #     ('Clinic','Clinic'),
    #     ('Hospital','Hospital'),
    #     ('Hospital Pharmacy','Hospital Pharmacy'),
    # )  
    name=models.CharField(_("Business Type"), max_length=50)

    class Meta:
        verbose_name = _("BusinessType")
        verbose_name_plural = _("BusinessTypes")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("BusinessType_detail", kwargs={"pk": self.pk})


class Company(
    CompanyMixin,
    # socialmedMixin,
    # to add django tenancy to here
    createdtimestamp_uid,
):  
    industry = models.ForeignKey(Industry, verbose_name=_("Industry"), on_delete=models.SET_NULL, blank=True, null=True)
    tradecountry=models.ForeignKey(Country, verbose_name=_("Primary Trade Country"), on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    payment = models.ForeignKey(
        PaymentClass, verbose_name=_("Payment Class"), on_delete=models.CASCADE
    )
    business_type=models.ForeignKey(BusinessType, verbose_name=_("Business Type"), on_delete=models.SET_NULL,blank=True, null=True)
    # company_logo=models.URLField(_("Company Logo"), max_length=200,blank=True, null=True)
    company_logo=models.CharField(_("Company Logo"), max_length=200,blank=True, null=True)
    # company_logo= models.ImageField(upload_to='complogo/',blank=True, null=True)     
    contact=models.ManyToManyField(Contact, verbose_name=_("Contacts"))
    # contact is to be fixed completely
    default_currency=CurrencyField(
        _("Default Currency"),
        default='GHS',
    )
    # create a new models.py for handling company-specific settings called config
    # such as default currency, tax rates, etc.
    
    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")

    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
        # prevent update of  default_currency
        if self._state.adding  and self.pk and not self.default_currency:
            # if the company already exists, do not change the default currency
            existing_company = Company.objects.filter(pk=self.pk).first()
            if existing_company:
                self.default_currency = existing_company.default_currency
        # if no default currency is set, use 'GHS' as the default
        elif not self.pk and not self._state.adding and not self.default_currency:
            # if the company is being created and no default currency is set, use 'GHS'
            self.default_currency = 'GHS'
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("Company_detail", kwargs={"pk": self.pk})



# 
#  
# create specific django models for specific 
# Clinic and Hospital Pharmacy and Pharmacy specific Models
# 
#
# 
# 
#   




class DocumentType(createtimstam_uid):
    name=models.CharField(_("Document Type"), max_length=50, unique=True)
    company=models.ForeignKey(Company, verbose_name=_("Company"), on_delete=models.CASCADE, blank=True, null=True)
    class Meta:
        verbose_name = _("DocumentType")
        verbose_name_plural = _("DocumentTypes")
        unique_together = ('name', 'company',)
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("DocumentType_detail", kwargs={"pk": self.pk})
class Document(createtimstam_uid):
    document_type=models.ForeignKey(DocumentType, verbose_name=_("Document Type"), on_delete=models.CASCADE,blank=True, null=True)
    document_file = models.FileField(
        _("Document File"),
        upload_to="documents/",
    )
    description=models.TextField(_("Description"), blank=True, null=True)
    custom_fields=models.JSONField(_("Custom Fields"), blank=True, null=True, default=dict)
    company=models.ForeignKey(Company, verbose_name=_("Company"), on_delete=models.CASCADE, )
    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    def __str__(self):
        return str(self.document_file)

    def get_absolute_url(self):
        return reverse("Document_detail", kwargs={"pk": self.pk})




```


```python

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.core.validators import RegexValidator
from addons.models import (
    CompanyMixin,
    createtimstam_uid,
)
# Create your models here.


class Country(models.Model):
    name=models.CharField(_("Name"), max_length=100)
    iso3=models.CharField(_("iso3"), max_length=3,blank=True, null=True)	
    iso2=models.CharField(_("iso2"), max_length=2,blank=True, null=True)
    numeric_code=models.CharField(_("Numeric Code"), max_length=6)
    phone_code=models.CharField(_("Phone Code"), max_length=5,blank=True, null=True)
    currency=models.CharField(_("Currency"), max_length=3,blank=True, null=True)
    currency_name=models.CharField(_("Currency Name"), max_length=50 ,blank=True, null=True)
    lat=models.DecimalField(_("Latitude"), max_digits=10, decimal_places=8,blank=True, null=True)
    lon=models.DecimalField(_("Longitude"), max_digits=11, decimal_places=8,blank=True, null=True)
    
    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Countrys")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Country_detail", kwargs={"pk": self.pk})

class State(models.Model):
    country=models.ForeignKey(Country, verbose_name=_("Country"), on_delete=models.CASCADE)
    name=models.CharField(_("State"), max_length=150)
    state_code=models.CharField(_("State Code"), max_length=5,blank=True, null=True)
    lat=models.DecimalField(_("Latitude"), max_digits=11, decimal_places=8,blank=True, null=True)
    lon=models.DecimalField(_("Longitude"), max_digits=11, decimal_places=8,blank=True, null=True)
    
    class Meta:
        verbose_name = _("State")
        verbose_name_plural = _("States")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("State_detail", kwargs={"pk": self.pk})


class City(models.Model):
    name=models.CharField(_("City"), max_length=150)
    state=models.ForeignKey(State, verbose_name=_("State"), on_delete=models.CASCADE)
    lat=models.DecimalField(_("Latitude"), max_digits=11, decimal_places=8,blank=True, null=True)
    lon=models.DecimalField(_("Longitude"), max_digits=11, decimal_places=8,blank=True, null=True)

    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Citys")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("City_detail", kwargs={"pk": self.pk})


class AddressType(createtimstam_uid):
    '''
    Includes but not limited to Home, Office , Landline, Future Location 
    '''

    name=models.CharField(_("Address Type"), max_length=50)

    class Meta:
        verbose_name = _("AddressType")
        verbose_name_plural = _("AddressTypes")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("AddressType_detail", kwargs={"pk": self.pk})
class PhoneType(createtimstam_uid):
    '''
    Includes but not limited to Mobile, Phone , ETC, Landline 
    '''

    name=models.CharField(_("Phone Type"), max_length=50)

    class Meta:
        verbose_name = _("PhoneType")
        verbose_name_plural = _("PhoneTypes")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("PhoneType_detail", kwargs={"pk": self.pk})

class EmailType(createtimstam_uid):
    '''
    Includes but not limited to Personal, Company, etc
    '''

    name=models.CharField(_("Email Type"), max_length=50)

    class Meta:
        verbose_name = _("EmailType")
        verbose_name_plural = _("EmailTypes")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("EmailType_detail", kwargs={"pk": self.pk})


class webType(createtimstam_uid):
    '''
    Includes but not limited to Social Media, Company Website, Blogs, etc
    '''

    name=models.CharField(_("Website Type"), max_length=50)

    class Meta:
        verbose_name = _("WebsiteType")
        verbose_name_plural = _("WebsiteTypes")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("WebsiteType_detail", kwargs={"pk": self.pk})





class Phone(createtimstam_uid):
    phonetype=models.ForeignKey(PhoneType, verbose_name=_("Phone Type"), on_delete=models.CASCADE,blank=True, null=True)
    phone = models.CharField(
        _("Phone"),
        max_length=50,
    )
    is_whatsapp=models.BooleanField(_("Is Whatsapp"), default=False)

    class Meta:
        verbose_name = _("Phone")
        verbose_name_plural = _("Phones")

    def __str__(self):
        return self.phone

    def get_absolute_url(self):
        return reverse("Phone_detail", kwargs={"pk": self.pk})

class Address(createtimstam_uid):
    addresstype=models.ForeignKey(AddressType, verbose_name=_("Address Type"), on_delete=models.CASCADE,blank=True, null=True)
    line=models.CharField(_("Line"), max_length=50)
    city=models.ForeignKey(City, verbose_name=_("City"), on_delete=models.CASCADE)
    # custom fields can include postal code, landmark, etc.
    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")

    def __str__(self):
        return f'{self.city.name}-{self.line}'

    def get_absolute_url(self):
        return reverse("Address_detail", kwargs={"pk": self.pk})
    
class Email(createtimstam_uid):
    email = models.EmailField(
        verbose_name=_("Email"),
    )
    emailType=models.ForeignKey(EmailType, verbose_name=_("Email Type"), on_delete=models.CASCADE,blank=True, null=True)
    class Meta:
        verbose_name = _("Email")
        verbose_name_plural = _("Emails")

    def __str__(self):
        return self.email

    def get_absolute_url(self):
        return reverse("Email_detail", kwargs={"pk": self.pk})


class Website(createtimstam_uid):
    website = models.URLField(
        verbose_name=_("Website"),
    )
    webtype=models.ForeignKey(webType, verbose_name=_("Website Type"), on_delete=models.CASCADE,blank=True, null=True)
    class Meta:
        verbose_name = _("Website")
        verbose_name_plural = _("Websites")

    def __str__(self):
        return self.website

    def get_absolute_url(self):
        return reverse("Website_detail", kwargs={"pk": self.pk})




# class Photos(createtimstam_uid):
#     # id=None
#     photo = models.CharField(_("Line"), max_length=100,unique=True,)

#     class Meta:
#         verbose_name = _("Photo")
#         verbose_name_plural = _("Photos")

#     def __str__(self):
#         return str(self.photo)

#     def get_absolute_url(self):
#         return reverse("Photo_detail", kwargs={"pk": self.pk})


# model for handling document management 


# after model migrations, load city, state and country data

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.apps import apps
import pandas as pd

@receiver(post_migrate)
def create_id_types(sender, **kwargs):
    # Replace 'yourapp' and 'id_type' with your actual app label and model name
    if sender.name == 'City':  # Only run on your app's migrations

        country_data = pd.read_csv('./testdummy/data/countries.csv')
        state_data = pd.read_csv('./testdummy/data/states.csv')
        city_data = pd.read_csv('./testdummy/data/cities.csv')
        # IdType = apps.get_model('yourapp', 'id_type')
        # default_types = [
        #     "National ID",
        #     "Passport",
        #     "Driver License",
        #     # Add more if needed
        # ]

        for index, row in country_data.iterrows():
            try:
                # Skip rows with missing essential data
                Country.objects.get_or_create(
                    name=row['name'],
                    code=row['code'],
                    iso3=row['iso3'],
                    iso2=row['iso2'],
                    numeric_code=row['numeric_code'],
                    phone_code=row['phone_code'],
                    currency=row['currency'],
                    currency_name=row['currency_name'],
                    lat=row['lat'],
                    lon=row['lon']
                )
            except:
                continue

        for index, row in state_data.iterrows():
            try:
                State.objects.get_or_create(
                    name=row['name'],
                    state_code=row['state_code'],
                    lat=row['lat'],
                    lon=row['lon'],
                    country=Country.objects.get(name=row['country'])
                )
            except:
                continue

        for index, row in city_data.iterrows():
            try:
                City.objects.get_or_create(
                    name=row['name'],
                    code=row['code'],
                    state=State.objects.get(name=row['state']),
                    lat=row['lat'],
                    lon=row['lon']
                )
            except:
                continue


```


```python

from django.db import models

# Create your models here.
from djmoney.models.fields import MoneyField

from invplan.models import order_document
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from addons.models import createtimstam_uid
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from company.models import Contact
from party.models import Staff,Client,Occupation
from django.core.exceptions import ValidationError
from company.models import Industry
from contact.models import City
from workflow.models import Workflow
# campaigns can be added later
# a model for territories
# https://deepwiki.com/go2ismail/Free-CRM/3-core-business-modules
# https://deepwiki.com/marmelab/atomic-crm/3-core-features
# https://deepwiki.com/frappe/crm/3-core-crm-entities
# https://deepwiki.com/marmelab/atomic-crm/2-data-model
# https://deepwiki.com/krayin/laravel-crm/2.2-lead-repository-and-data-structure
# https://deepwiki.com/Bottelet/DaybydayCRM/2.1-core-models-and-relationships
# https://deepwiki.com/krayin/laravel-crm/1.1-system-architecture

class Territory(createtimstam_uid):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, verbose_name=_("Staff"),)
    city = models.ManyToManyField(City, verbose_name=_("Cities"), blank=True, related_name="territories")
    class Meta:
        verbose_name = _("Territory")
        verbose_name_plural = _("Territories")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Territory_detail", kwargs={"pk": self.pk})

# tasks and activities can be added later


# salemember
# sale team

# sale team
class SaleMember(createtimstam_uid):
    id=None
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, verbose_name=_("Staff"), primary_key=True, related_name="sale_memberships")
    team_lead = models.BooleanField(default=False)
    assigned_territories = models.ManyToManyField(Territory, verbose_name=_("Assigned Territories"), blank=True, related_name="sale_members")
    creator = models.ForeignKey(Staff, on_delete=models.PROTECT, verbose_name=_("Staff"),related_name='created_sale_members')
    assistants = models.ManyToManyField('self', verbose_name=_("Assistants"), blank=True, )
    status = models.CharField(_("Status"), max_length=50, choices=(
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ), default='active')
    # assigned_tasks= models.ManyToManyField(Workflow, verbose_name=_("Assigned Tasks"), blank=True, related_name="sale_members_tasks")
    class Meta:
        verbose_name = _("Sale Member")
        verbose_name_plural = _("Sale Members")

    def __str__(self):
        return f"{self.staff.user.get_full_name()}"

    def get_absolute_url(self):
        return reverse("SaleMember_detail", kwargs={"pk": self.pk})

class SaleTeam(createtimstam_uid):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    team_leads = models.ManyToManyField( SaleMember, verbose_name=_("Team Leads"), blank=True, related_name="crm_team_leads",limit_choices_to={'team_lead': True} )
    members = models.ManyToManyField( SaleMember, verbose_name=_("Members"), blank=True, related_name="crm_teams",  )
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, verbose_name=_("Staff"),)
    assigned_territories = models.ManyToManyField(Territory, verbose_name=_("Assigned Territories"), blank=True, related_name="sales_teams")
    # assigned_tasks= models.ManyToManyField(Workflow, verbose_name=_("Assigned Tasks"), blank=True, related_name="sale_teams_tasks")
    
    def save(self, *args, **kwargs):
        # ensure that team lead is always a member of the team
        # if self.team_leads and self.team_leads.all() not in self.members.all():
        #     self.members.add(self.team_leads.all())
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Team")
        verbose_name_plural = _("Teams")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Team_detail", kwargs={"pk": self.pk})

# sales team maps to sales rep through a many to many relationship
# a sale rep can have multiple sale teams and a sale team can have multiple
# sale rep

# tags are an array of strings

# pipeline of the lead
class Pipeline(createtimstam_uid):
    # pipeline stages are the various stages a lead goes through before becoming a customer and closing a sale as well as tracking lost leads
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, verbose_name=_("Staff"),)
    # previous_stages = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='next_stages')
    class Meta:
        verbose_name = _("Pipeline")
        verbose_name_plural = _("Pipelines")

    # must only have one final stage
    def save(self, *args, **kwargs):
        # if self.final_stage:
        #     Pipeline.objects.filter(final_stage=True).update(final_stage=False)
        #     self.previous_stages = None
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name



class stage(createtimstam_uid):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, verbose_name=_("Pipeline"), related_name="stages")
    sequence = models.IntegerField(_("Sequence"), default=1,)
    is_won= models.BooleanField(_("Is Won Stage"), default=False)
    is_lost= models.BooleanField(_("Is Lost Stage"), default=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    probability = models.IntegerField(_("Probability (%)"), default=0)
    tasks= models.ManyToManyField(Workflow, verbose_name=_("Assigned Tasks"), blank=True, related_name="prospect_assigned_tasks")   
    # workflows 

    class Meta:
        verbose_name = _("Stage")
        verbose_name_plural = _("Stages") 
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse("stage_detail", kwargs={"pk": self.pk})
class PipelineTransition(createtimstam_uid):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, verbose_name=_("Pipeline"), related_name="pipe_line_transitions")
    from_stage = models.ForeignKey(stage, on_delete=models.PROTECT, verbose_name=_("From Stage"), related_name="from_stage_transitions")
    to_stage = models.ForeignKey(stage, on_delete=models.PROTECT, verbose_name=_("To Stage"), related_name="to_stage_transitions")
    
    # conditions can be added later


    class Meta:
        verbose_name = _("Pipeline Transition")
        verbose_name_plural = _("Pipeline Transitions")
        unique_together = ('pipeline', 'from_stage', 'to_stage',)
    def __str__(self):
        return f"{self.pipeline.name}: {self.from_stage.name} -> {self.to_stage.name}"




class Campaign(createtimstam_uid):
    # campanign types can be added later
    # a campaign can be linked to a marketing activity later
    
    statuses=[
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('postponed', 'Postponed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(_("Status"), max_length=20, choices=statuses, default='planned')
    approval_staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, verbose_name=_("Approval Staff"), related_name="approval_campaigns", null=True, blank=True)
    approval_status = models.CharField(_("Approval Status"), max_length=20, choices=[
        ('pending', 'Pending'),
        ('needs_revision', 'Needs Revision'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    # related task or schedule plan can be added later

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    budget = MoneyField(
        _("Budget"),
        max_digits=20,
        decimal_places=2,
        default=0,default_currency='GHS'
    )
    assigned_tasks= models.ManyToManyField(Workflow, verbose_name=_("Assigned Tasks"), blank=True, related_name="campaign_assigned_tasks")

    # add documents field later
    # add deadline for approval and rejection later
    # add actual cost and actual revenue later
    # target_audience can be optimized to a many to many relationship later
    targetted_territories= models.ManyToManyField(Territory, verbose_name=_("Targetted Territories"), blank=True, related_name="campaign_targeted_territories")
    # campaigns can lead to the creation of leads and prospects and prospect companies
    
    # target_audience = models.TextField(blank=True, null=True)
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, verbose_name=_("Created By"), related_name="created_campaigns", )
    projected_reach = models.IntegerField(_("Projected Reach"), blank=True, null=True)
    progress = models.IntegerField(_("Progress (%)"), default=0) 
    # progress will be calculated based on tasks completed and activities done
    projected_revenue = MoneyField(
        _("Projected Revenue"),
        max_digits=20,
        default=0,default_currency='GHS',
        decimal_places=2,
    )
    assigned_sales_team = models.ManyToManyField(SaleTeam, verbose_name=_("Assigned Sales Team"), blank=True,related_name="assigned_campaigns")
    assigned_sales_rep = models.ManyToManyField(SaleMember, verbose_name=_("Assigned Sales Member"), blank=True, related_name="assigned_campaigns")
    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Campaign_detail", kwargs={"pk": self.pk})



class Prospect_Company(createtimstam_uid):

    name = models.CharField(_("Company Name"), max_length=200,unique=True)
    description = models.TextField(blank=True, null=True)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, verbose_name=_("Industry"), blank=True, null=True)
    contact = models.ManyToManyField(Contact,  verbose_name=_("Contact"), blank=True, )
    additional_info = models.JSONField(blank=True, null=True, default=dict)
    # logo = models.ImageField(upload_to='prospect_company_logos/', blank=True, null=True)
    size = models.CharField(_("Company Size"), max_length=100, blank=True, null=True,choices=[
        ('x_small', 'Extra Small (1-24 employees)'),
        ('small', 'Small (25-50 employees)'),
        ('medium', 'Medium (51-250 employees)'),
        ('large', 'Large (251+ employees)'),
    ])
    assigned_sales_team = models.ManyToManyField(SaleTeam, verbose_name=_("Assigned Sales Team"), blank=True)
    assigned_sales_rep = models.ManyToManyField(SaleMember, verbose_name=_("Assigned Sales Rep"), blank=True, related_name="assigned_prospect_companies")
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, verbose_name=_("Staff"), related_name="created_prospect_companies")
    # targetted_territories= 
    territory = models.ManyToManyField(Territory, verbose_name=_("Territories"), blank=True, related_name="prospect_companies_territories")
    # documents= models.ManyToManyField('addons.Document', verbose_name=_("Documents"), blank=True, related_name="prospect_companies_documents")
    campaign= models.ManyToManyField(Campaign, verbose_name=_("Campaign"), related_name="prospect_companies", blank=True)

    class Meta:
        verbose_name = _("Prospect Company")
        verbose_name_plural = _("Prospect Companies")



    def __str__(self):
        return self.name

    # a foreign key showing the sales rep assigned to the prospect company can be added later
    # a foreign key showing which user created 
    def get_absolute_url(self):
        return reverse("Prospect_Company_detail", kwargs={"pk": self.pk})


class Prospect(createtimstam_uid):
    # Prospect is a person or a contact who has shown interest in a company's products or services and is considered a potential customer.
    # Prospects are typically in the early stages of the sales funnel and may have engaged with the company through various channels such as website visits, inquiries, or marketing campaigns.
    # They are not yet qualified leads but have the potential to become customers with further nurturing and engagement.
    # Managing prospects effectively is crucial for converting them into paying customers.
    # Prospects often require targeted communication and follow-up to move them through the sales process.
    # Prospects can be individuals or representatives of organizations, depending on the nature of the business.
    # Prospects become customers when they make a purchase or engage in a business transaction with the company.
    staff=models.ForeignKey(Staff, on_delete=models.PROTECT, verbose_name=_("Staff"), related_name="created_prospects")
    company = models.ForeignKey(Prospect_Company, on_delete=models.CASCADE, verbose_name=_("Prospect Account"), blank=True, null=True) #prospect company will be optimized to only one 
    username = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255,null=True, blank=True)
    last_name = models.CharField(max_length=255,null=True, blank=True)
    role = models.ForeignKey(Occupation, on_delete=models.CASCADE, verbose_name=_("Role"), blank=True, null=True)
    # avatar = models.ImageField(upload_to='prospect_avatars/', blank=True, null=True)
    territory = models.ForeignKey(Territory, on_delete=models.SET_NULL, verbose_name=_("Territory"), related_name="territory_prospects", blank=True, null=True)
    assigned_sales_team = models.ManyToManyField(SaleTeam, verbose_name=_("Assigned Sales Team"), blank=True,)#related_name="assigned_prospects"
    assigned_sales_rep = models.ManyToManyField(Staff, verbose_name=_("Assigned Sales Rep"), blank=True, related_name="assigned_prospects")
    contact = models.ManyToManyField(Contact,  verbose_name=_("Contact"), blank=True)
    client_user= models.ForeignKey(Client, on_delete=models.SET_NULL, verbose_name=_("Client User"), blank=True, null=True)
    status = models.CharField(_("Status"),choices=[
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('unqualified', 'Unqualified'),
        ('converted', 'Converted'),
        ('lost', 'Lost')], 
        max_length=100,
        default='new'
    )
    additional_info = models.JSONField(blank=True, null=True, default=dict)
    campaign= models.ForeignKey(Campaign, on_delete=models.SET_NULL, verbose_name=_("Campaign"), related_name="prospects", blank=True, null=True)
    assigned_departments= models.ManyToManyField('department.Department', verbose_name=_("Assigned Departments"), blank=True, )
    tasks= models.ManyToManyField(Workflow, verbose_name=_("Assigned Tasks"), blank=True, )   

    # created_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, verbose_name=_("Created By"), related_name="created_prospects", null=True)

    # sales rep assigned to the prospect
    # sales team assigned to the prospect
    # user creating the prospect
    # , Estimated Closing Date, Actual Closing Date
    # expected_revenue
    # expected_close_date

    # closing_probability = models.IntegerField(_("Closing Probability (%)"), default=0)
    # closed_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, verbose_name=_("Closed By"), related_name="closed_prospects", null=True, blank=True)
    # close_date = models.DateField(_("Close Date"), blank=True, null=True)
    # documents= models.ManyToManyField('addons.Document', verbose_name=_("Documents"), blank=True, related_name="prospect_documents")

    class Meta:

        verbose_name = _("Prospect")
        verbose_name_plural = _("Prospects")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Prospect_detail", kwargs={"pk": self.pk})

# create the propspect pipeline stages model 
class ProspectPipelineStage(createtimstam_uid):
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, verbose_name=_("Prospect"), related_name="pipeline_stages")
    pipeline = models.ForeignKey(Pipeline, on_delete=models.PROTECT, verbose_name=_("Pipeline"))
    stage = models.ForeignKey(stage, on_delete=models.PROTECT, verbose_name=_("Stage"))
    status = models.CharField(_("Status"), max_length=50, choices=(
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ), default='in_progress')
    start_date = models.DateTimeField(_("Start Date"), auto_now_add=True)
    end_date = models.DateTimeField(_("End Date"), blank=True, null=True)
    sales_rep = models.ForeignKey(SaleMember, on_delete=models.SET_NULL, verbose_name=_("Sales Rep"), related_name="sales_rep_pipeline_stages", blank=True, null=True)
    class Meta:
        verbose_name = _("Prospect Pipeline Stage")
        verbose_name_plural = _("Prospect Pipeline Stages")

    def __str__(self):
        return f"{self.prospect.name} - {self.stage.name}"

    def get_absolute_url(self):
        return reverse("ProspectPipelineStage_detail", kwargs={"pk": self.pk})
# class (createtimstam_uid):

# class ActivityType(createtimstam_uid):
#     name = models.CharField(max_length=255, unique=True)
#     description = models.TextField(blank=True, null=True)

#     class Meta:
#         verbose_name = _("Activity Type")
#         verbose_name_plural = _("Activity Types")

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse("ActivityType_detail", kwargs={"pk": self.pk})

# Activities
# class Activity(createtimstam_uid):
#     activity_type = models.ForeignKey(ActivityType, on_delete=models.CASCADE, verbose_name=_("Activity Type"))
#     name = models.CharField(max_length=255, unique=True)
#     description = models.TextField(blank=True, null=True)
#     created_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, verbose_name=_("Created By"), related_name="created_activities", null=True)


#     class Meta:
#         verbose_name = _("Activity")
#         verbose_name_plural = _("Activities")

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse("Activity_detail", kwargs={"pk": self.pk})


# class Tasks(createtimstam_uid):
#     name = models.CharField(max_length=255, unique=True)
#     description = models.TextField(blank=True, null=True)
#     created_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, verbose_name=_("Created By"), related_name="created_tasks", null=True)


#     class Meta:
#         verbose_name = _("Task")
#         verbose_name_plural = _("Tasks")

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse("Tasks_detail", kwargs={"pk": self.pk})

# class TaskActivityMapping(createtimstam_uid):
#     task = models.ForeignKey(Tasks, on_delete=models.CASCADE, verbose_name=_("Task"), related_name="task_activities")
#     activity = models.ForeignKey(Activity, on_delete=models.CASCADE, verbose_name=_("Activity"), related_name="activity_tasks")
#     previous_tasks = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='next_tasks')
#     next_tasks = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='previous_tasks')
#     class Meta:
#         verbose_name = _("Task Activity Mapping")
#         verbose_name_plural = _("Task Activity Mappings")
 
#     def __str__(self):
#         return f"Task: {self.task.name} - Activity: {self.activity.activity_type.name}"

#     def get_absolute_url(self):
#         return reverse("TaskActivityMapping_detail", kwargs={"pk": self.pk})

# lead Tasks and Activities can be added later 

# Sale Team Approvals and Approval Requests can be added later


class Deal(createtimstam_uid):
    STAGE_CHOICES = [
        ('prospecting', 'Prospecting'),
        ('negotiation', 'Negotiation'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ]
    # name = models.CharField(max_length=255)
    # related task or schedule plan can be added later
    # description = models.TextField(blank=True, null=True)

    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, related_name='deals')
    deal_valuation =  MoneyField(
        _("Deal Valuation"),
        max_digits=20,
        decimal_places=2,
        default=0,default_currency='GHS'
    )
    status = models.CharField(_("Status"), max_length=20, choices=STAGE_CHOICES, default='prospecting')
    close_date = models.DateField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    # a deal should create an order when prospect is won
    # pending deals are technically quotes and should be converted to orders when won
    # an order is created when a deal is created and the order becomes a sale document when the deal is won
    order = models.ForeignKey(order_document, on_delete=models.CASCADE, verbose_name=_("Order"), related_name="deal_order",)
    tasks= models.ManyToManyField(Workflow, verbose_name=_("Assigned Tasks"), blank=True, related_name="deal_assigned_tasks")
    def __str__(self):
        return f"Deal: {self.name} - Valuation: {self.deal_valuation}"

    def get_absolute_url(self):
        return reverse("Deal_detail", kwargs={"pk": self.pk})

    class Meta:
        verbose_name = _("Deal")
        verbose_name_plural = _("Deals")


# class DealActivity_Tasks(models.Model):
#     deal = models.ForeignKey(Deal, on_delete=models.CASCADE, verbose_name=_("Deal"), related_name="deal_activities_tasks")
#     activity = models.ForeignKey(Activity, on_delete=models.CASCADE, verbose_name=_("Activity"))
#     task = models.ForeignKey(Tasks, on_delete=models.CASCADE, verbose_name=_("Task"))
#     description = models.TextField(blank=True, null=True)
#     timestamp = models.DateTimeField(auto_now_add=True)
#     status = models.CharField(max_length=50, choices=[
#         ("planned", _("Planned")),
#         ("in_progress", _("In Progress")),
#         ("completed", _("Completed")),
#         ("cancelled", _("Cancelled")),
#     ], default="planned")

#     class Meta:
#         verbose_name = _("Deal Activity Task")
#         verbose_name_plural = _("Deal Activity Tasks")

#     def __str__(self):
#         return f"DealActivity_Tasks: {self.deal} - Activity: {self.activity.activity_type.name} - Task: {self.task.name}"

#     def get_absolute_url(self):
#         return reverse("DealActivity_Tasks_detail", kwargs={"pk": self.pk})


# # deal details 
# class DealDetails(models.Model):
#     deal = models.ForeignKey(Deal, on_delete=models.CASCADE, verbose_name=_("Deal"), related_name="deal_details")
#     detail_key = models.CharField(max_length=255)
#     detail_value = models.TextField()

#     class Meta:
#         verbose_name = _("Deal Detail")
#         verbose_name_plural = _("Deal Details")

#     def __str__(self):
#         return f"DealDetail: {self.deal} - {self.detail_key}: {self.detail_value}"
```


```python
from django.db import models

# Create your models here.
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.exceptions import ValidationError
from accounts.models import Account, Charts_of_account,Tax
from django.contrib.postgres.fields import ArrayField

from django.urls import reverse
from contact.models import Phone,Address,Email,Website

from testdummy.dummyvaluescreator import generate_random_names
from addons.models import createdtimestamp_uid,activearchlockedMixin
from company.models import Company,Contact
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from addons.models import (
    addressMixin,
    phonenumberMixin,
    socialmedMixin,
    createdtimestamp_uid,
)
from djmoney.models.fields import MoneyField


class Department(createdtimestamp_uid,activearchlockedMixin, models.Model):
    choice=(
        # ("B2B", "B2B"),
        # ("B2C", "B2C"),
        ("Wholesale Unit", "Wholesale Unit"),
        ("Retail Unit", "Retail Unit"),
        ("Manufacturing Unit", "Manufacturing Unit"),
    )
    staff = models.ForeignKey(
        'party.Staff',
        verbose_name=_("Staff"),
        on_delete=models.PROTECT,
        related_name="+",
    )
    
    departmenttype=models.CharField(_("Department Role"), max_length=50,choices=choice)
    name = models.CharField(_("Department Name"), max_length=50)
    description = models.TextField(_("Description"), blank=True, null=True)
    base_markup = models.DecimalField(
        _("Base Markup"), max_digits=5, decimal_places=2,default=0
    )
    is_marked_up_from = models.ForeignKey(
        "self",
        verbose_name=_("Is Marked Up From"),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="markedpufrom",
    )
    
    is_saledepartment=models.BooleanField(_("sale Department"),default=False) 
    is_onlinesaledepartment=models.BooleanField(_("Online Sale Department"),default=False)  #determines if this branches under this department can access the online sales and Make sales via the online sales...Members withing this department can have multiple sale points or Tender recieving points in a branch
    defaultonlinedepartment=models.BooleanField(_("Default online Department"), default=False) #must have online department shop true and must deactivate all other defaults... Default department prices and products to be shown to unauthenticated users when browsing the online shop.  
    is_creditsale_allowed=models.BooleanField(_("Credit Sale All"), default=False)
    contact=models.ManyToManyField(Contact, verbose_name=_("Contact"),blank=True)
    def save(self, *args, **kwargs):
        # if self.id and self.id
        if self.is_marked_up_from and self.is_marked_up_from.pk == self.pk:
            raise ValidationError('You can\'t have yourself as a parent!')
        if self.is_onlinesaledepartment and not self.is_saledepartment:
            raise ValidationError(
                'You can\'t have an online sale department without a sale department!'
            )
        if self.defaultonlinedepartment and not self.is_onlinesaledepartment:
            raise ValidationError(
                'You can\'t have a default online department without an online sale department!'
            )
        if self.is_creditsale_allowed and not self.is_saledepartment:
            raise ValidationError(
                'You can\'t allow credit sales without a sale department!'
            )
        if self.is_onlinesaledepartment and not self.is_saledepartment:
            raise ValidationError(
                'You can\'t have an online sale department without a sale department!'
            )
        if self.defaultonlinedepartment:
            Department.objects.filter(
                is_onlinesaledepartment=True,
                defaultonlinedepartment=True
            ).update(defaultonlinedepartment=False)

        super(Department, self).save(*args, **kwargs)


    class Meta:
        verbose_name = _("department")
        verbose_name_plural = _("departments")
        unique_together = ("departmenttype",'name')

    def __str__(self):
        return f"{self.name} - {self.departmenttype}"

    def get_absolute_url(self):
        return reverse("department_detail", kwargs={"pk": self.pk})

# make Ghana Card Identification required for all online shop experiences for pharmaceuticals
# all others purchase make optional for the retail shop
# Use Ghana card verification process to verify and link users on the online shop buying pharmaceuticals 
# And track every customer's medical history etc
#  

# Branchwise Shifts

# shift types
class Shift(createdtimestamp_uid, ):

    # types of shifts
    shift_types = models.CharField(_("Shift Types"), max_length=50,choices=(
        ("Morning Shift", "Morning Shift"),
        ("Afternoon Shift", "Afternoon Shift"),
        ("Evening Shift", "Evening Shift"),
        ("Night Shift", "Night Shift"),
    ))
    start_time = models.TimeField()
    end_time = models.TimeField()
    department = models.ForeignKey(
        Department,  
        verbose_name=_("Department"),
        on_delete=models.CASCADE,
    ) 
    staff = models.ForeignKey(
        'party.Staff',
        verbose_name=_("Staff"),
        on_delete=models.PROTECT,
        related_name="+",
    )
    break_duration_minutes = models.PositiveIntegerField(
        _("Break Duration"),
        blank=True,
        null=True,
        help_text="Break duration in minutes during the shift.",
        default=0,
    )

    class Meta:
        verbose_name = _("Shift")
        verbose_name_plural = _("Shifts")
        unique_together = ("shift_types", "department")

    def __str__(self):
        return self.shift_types

    def get_absolute_url(self):
        return reverse("Shift_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if self.start_time >= self.end_time:
            raise ValidationError("Shift start time must be before end time.")
        super(Shift, self).save(*args, **kwargs)



class Branch( activearchlockedMixin,createdtimestamp_uid):

    department = models.ForeignKey(
        Department,
        verbose_name=_("Department"),
        on_delete=models.PROTECT,  ##add a limit choices to and limit choices to only sale departments
    )
    # is_active = models.BooleanField(_("Is Active"), default=True)
    staff = models.ForeignKey(
        'party.Staff',
        verbose_name=_("Staff"),
        on_delete=models.PROTECT,
        related_name="+",
    )
    name = models.CharField(_("Branch Name"), max_length=50)
    warehouse_unit = models.ForeignKey(
        "self",
        verbose_name=_("Warehouse Unit/Primary Supply Unit"),
        on_delete=models.PROTECT,
        limit_choices_to={
            "is_warehouse": True,
        },
        blank=True,
        null=True,
    )
    is_warehouse = models.BooleanField(
        _("Is A Primary Storage or Supply Warehouse"), default=False
    )
    address = models.ForeignKey(
        Address,
        verbose_name=_("Branch Address"),
        on_delete=models.PROTECT,
    )
    contact = models.ManyToManyField(Contact, verbose_name=_("Contact"), blank=True)
    # branchaccount = models.ForeignKey(
    branchaccount=models.ManyToManyField(
        Account,
        verbose_name=_("Branch Account"),
        blank=True,
        related_name="branchaccount",
    )
    tax=models.ManyToManyField(Tax, verbose_name=_("Default Sale Taxes"),blank=True)
    avatar = models.CharField(_("Avatar Image"), max_length=255, blank=True, null=True)
    

    class Meta:
        verbose_name = _("Branch")
        verbose_name_plural = _("Branchs")
        unique_together = ("name", "department")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Branch_detail", kwargs={"pk": self.pk})



# class RoomActivity(createdtimestamp_uid):

#     # default_activity_set=(
#     #     ('project_discussion', 'Project Discussion'),
#     #     ('performance_review', 'Performance Review'),
#     #     ('training_session', 'Training Session'),
#     #     ('client_meeting', 'Client Meeting'),
#     #     ('team_building', 'Team Building'),
#     #     ('interview', 'Interview'),
#     #     ('workshop', 'Workshop'),
#     #     ('seminar', 'Seminar'),
#     #     ('brainstorming_session', 'Brainstorming Session'),
#     #     ('presentation', 'Presentation'),
#     # )
#     default_activity_set=(
#         ('Project Discussion', 'Project Discussion'),
#         ('Performance Review', 'Performance Review'),
#         ('Training Session', 'Training Session'),
#         ('Client Meeting', 'Client Meeting'),
#         ('Team Building', 'Team Building'),
#         ('Interview', 'Interview'),
#         ('Workshop', 'Workshop'),
#         ('Seminar', 'Seminar'),
#         ('Brainstorming Session', 'Brainstorming Session'),
#         ('Presentation', 'Presentation'),
#     )
#     # relate an activity to a permission and role for access control recommendations
#     name = models.CharField(_("Activity Type"), max_length=100, unique=True,choices=default_activity_set)
#     # slug = models.SlugField(_("Slug"), max_length=100, unique=True)
#     description = models.TextField(_("Description"), blank=True, null=True)
#     # manytomany to self
#     staff = models.ForeignKey(
#         'party.Staff',
#         verbose_name=_("Staff"),
#         on_delete=models.PROTECT,
#         related_name="+",
#     )

#     class Meta:
#         verbose_name = _("Room Activity")
#         verbose_name_plural = _("Room Activities")

#     def __str__(self):
#         return self.name
#     def save(self, *args, **kwargs):
#         super().save(*args, **kwargs)

#     def get_absolute_url(self):
#         return reverse("RoomActivity_detail", kwargs={"pk": self.pk})



# Rooms are entities used to manage physical spaces within an organization, such as meeting rooms, conference rooms, training rooms, etc.
# These models will help in scheduling and managing the use of these spaces for various HRM activities like meetings, interviews, training sessions, etc.
# rooms can be linked to locations and branches to provide a comprehensive view of the organization's physical infrastructure.
# rooms can have attributes like capacity, equipment available, and booking status to facilitate efficient resource management.
# rooms can be booked by employees or departments for specific time slots, ensuring optimal utilization of available spaces.
# rooms can have associated costs for usage, which can be tracked and billed to the respective departments or projects.
# rooms can have maintenance schedules to ensure they are kept in good condition for use. Maintenance activities can be logged and tracked. They
# rooms can have access controls to restrict usage to authorized personnel only.
# rooms have activities associated with them, such as meetings, interviews, training sessions, etc.
# rooms can also be linked to events and meetings to facilitate scheduling and resource allocation.

class Room(createdtimestamp_uid):
    name = models.CharField(_("Room Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    cost_rate= models.CharField(_("Cost Rate Type"), max_length=20, choices=[
        ('fixed', 'Fixed Cost Per Use'),
        ('hourly', 'Hourly Cost Per Use'),
        ('daily', 'Daily Cost Per Use'),
        ('none', 'No Cost'),
        ('weekly', 'Cost Per Week'),
        ('monthly', 'Cost Per Month'),
        ('yearly', 'Cost Per Year'),
    ], default='none')
    assigned_cost= MoneyField(_("Cost"), max_digits=10, decimal_places=2, default_currency='GHS', default=0)
    staff = models.ForeignKey(
        'party.Staff',
        verbose_name=_("Staff"),
        on_delete=models.PROTECT,
    )
    # if a cost per hour is defined then cost per use will be calculated based on the duration of the meeting or event
    floor_number = models.CharField(_("Floor Number"), max_length=10, null=True, blank=True, default="0")
    # location=models.ManyToManyField(Contact, verbose_name=_("Contact"),blank=True,limit_choices_to={'content_type__model':'address'})
    location=models.ForeignKey(Address, verbose_name=_("Address"), on_delete=models.PROTECT)
    # 'content_type':'Address'
    capacity = models.PositiveIntegerField(_("Capacity"), default=0)
    restricted_access = models.BooleanField(_("Restricted Access"), default=False)
    activities= ArrayField(
        models.CharField(max_length=100, choices=(
            ('Project Discussion', 'Project Discussion'),
            ('Performance Review', 'Performance Review'),
            ('Training Session', 'Training Session'),
            ('Client Meeting', 'Client Meeting'),
            ('Team Building', 'Team Building'),
            ('Interview', 'Interview'),
            ('Workshop', 'Workshop'),
            ('Seminar', 'Seminar'),
            ('Brainstorming Session', 'Brainstorming Session'),
            ('Presentation', 'Presentation'),
        )),
        verbose_name=_("Activities"),
        blank=True,
        default=list,
    )
    # activities = models.ManyToManyField(RoomActivity, verbose_name=_("Activities"), blank=True,)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('available', 'Available'), 
        ('unavailable', 'Unavailable'),
    ], default='available')
    # booking status is a computed field based on scheduled meetings and events and when the if the
    # facilities/equipment/infrastructure available in the room makes a user more informed when booking the room
    assigned_branch=models.ManyToManyField(
        Branch,
        verbose_name=_("Assigned Branches"),
        blank=True,
    )
    assigned_staff=models.ManyToManyField(
        'party.Staff',
        verbose_name=_("Assigned Staff"),
        blank=True,
        related_name="roomassignedstaff",
    )
    # it is recommended that rooms are linked to branches for better management of physical spaces within the organization.
    # each department can have multiple branches and each branch can have multiple rooms.


    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")

    def save(self, *args, **kwargs):
        if self.cost_rate != 'none' and (self.assigned_cost is None or self.assigned_cost.amount <= 0):
            raise ValidationError("Assigned cost must be greater than zero for the selected cost rate type.")
        # if self.cost_rate == 'none':
        #     self.assigned_cost = None

        # if self.restricted_access and self.assigned_staff.count() == 0:
        #     raise ValidationError("Restricted access rooms must have assigned staff.")
            
        # if self.capacity < 0:
        #     raise ValidationError("Room capacity cannot be negative.")

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Room_detail", kwargs={"pk": self.pk})


class Shelfing(createdtimestamp_uid, ):
    branch = models.ForeignKey(
        Branch, verbose_name=_("Branch"), on_delete=models.CASCADE,related_name='branchshelf'
    )
    room= models.ForeignKey(
        Room, verbose_name=_("Room"), on_delete=models.CASCADE,related_name='roomshelf', null=True, blank=True
        # make room optional to allow for general shelfing in the branch
        # this will help in organizing shelfing either within specific rooms or generally within the branch
    )
    shelf = models.CharField(
        _("Shelf Number"),
        max_length=50,
        help_text="A retailer assigned shelf number classification",
    )


    class Meta:
        verbose_name = _("shelfing")
        verbose_name_plural = _("shelfings")
        unique_together = ("branch", "shelf", )

    def __str__(self):
        return self.shelf

    def get_absolute_url(self):
        return reverse("shelfing_detail", kwargs={"pk": self.pk})




# sale


from accounts.models import Charts_of_account
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify  # new
# from inventory.models import (
#     Manufacturer,
#     ManufacturerBrand,
#     ProductsCategory,
#     Item,
#     Form,
#     PackSize,
#     Barcode,
#     item_pricing_department,
#     ItemLot,
#     ItemInventoryLot,
    
# )
from party.models import Occupation
from contact.models import Country,State,City,AddressType
from testdummy.dummyvaluescreator import (
    generate_random_email,
    generate_random_names,
    generate_random_date,
    generate_random_datetime,
    generate_random_selection,
    generate_random_decimal,
    generate_random_boolean,
    generate_random_integer,
    generate_random_barcode,
    generate_random_date_man,
)
import pandas as pd



@receiver(post_save, sender=Company)
def load_initial_account_data(sender, instance=None, created=False, **kwargs):
    if created:
        
        for a in ["Billing","Shipping","Contact"]:
            AddressType.objects.get_or_create(
                name=a,
            )
        

            
        # for socialtype, baseurl in social_media_urls.items():
        #     socialmed.objects.get_or_create(
        #         socialtype=socialtype,
        #         baseurl=baseurl,
        #     )

            
    # https://www.xero.com/guides/journal-entry/
    # Check if the current migration is for MyModel
    ## alter code and use bulk create
    company = instance  # Get the company instance
    # any thing increasing assets and expenses we debit
    # increase in liabilities income and capital credit
    if created:
        
        ASSETS = (
            "Cash",  # debit
            "Accounts Receivables",  # debit
            # "Allowance for Doubtful Accounts",#
            "Inventory",  # debit
            # "Uncollectibles",
            "Prepaid Expense",  # debit
            "Other Liquid Assets",
            "Notes Receivable",  # debit
            "Land",  # debit
            "Securities",
            "Buildings",  # debit
            "Buildings - Accum. Depreciation",  # credit
            "Plant",  # debit
            "Vehicles - Accum. Depreciation",
            "Vehicles",  # debit
            "Plant - Accum. Depreciation",
            "Equipment",  # debit
            "Supplies",  # debit
            "Equipment - Accum. Depreciation",  # credit
            "Intangible Assets",
            "Intangible Assets - Accum. Amortization",  # credit
            "Other Assets",
        )
        assets = 10100000
        Assets = [
            Charts_of_account(
                account_type="Assets",
                account_balance_type="Debit",
                # slug=slugify(str(a)),
                name=str(a),
                acc_number=assets + i * 1000,
            )
            for i, a in enumerate(ASSETS)
        ]
        Charts_of_account.objects.bulk_create(Assets)
        print("Company Accounts Assets created")

        CURRENT_LIABILITIES = (
            # "Liabilities",#credit
            "Accounts Payable",  # credit
            "Wages Payable",  # credit
            "Interest Payable",  # credit
            "Taxes Payable",  # credit
            "Notes Payable",  # credit
            "Prepaid Income",  # credit
            "Deferred Revenue",  # credit
            "Other Liabilities",  # credit
            "Bonds Payable",  # credit
            "Mortgage Payable",  # credit
            "Discount on Bonds Payable",  # credit
            "Tips Payable",  # credit
        )
        liabilities = 20100000
        LIABILITIES = [
            Charts_of_account(
                account_type="Liabilities",
                account_balance_type="Credit",
                # slug=slugify(str(a)),
                name=str(a),
                acc_number=liabilities + i * 2000,
            )
            for i, a in enumerate(CURRENT_LIABILITIES)
        ]
        Charts_of_account.objects.bulk_create(LIABILITIES)
        print("Company Accounts Liabilities created")

        EQUITY = (
            "Capital",  # credit
            "Common Stock",  # credit
            "Preferred Stock",  # credit
            "Retained Earnings",  # credit
            "Treasury Stock",  # credit
            "Other Equity Adjustments",  # credit
            "Dividends & Distributions to Shareholders",  # credit
        )
        equity = 30100000
        Equity = [
            Charts_of_account(
                account_type="Capital/Equity",
                account_balance_type="Credit",
                # slug=slugify(str(a)),
                name=str(a),
                acc_number=equity + i * 1000,
            )
            for i, a in enumerate(EQUITY)
        ]
        Charts_of_account.objects.bulk_create(Equity)
        print("Company Accounts Equity created")

        Revenues_Income = (
            "Revenue/Income",  # credit
            "Operational Income",  # credit
            "Investing/Passive Income",  # credit
            "Interest Income",  # credit
            "Capital Gain/Loss Income",  # credit
            "Income_Other",  # credit
            "Interest Revenue",  # credit
        )
        reven = 40100000
        Revenues = [
            Charts_of_account(
                account_type="Revenues/Income",
                account_balance_type="Credit",
                # slug=slugify(str(a)),
                name=str(a),
                acc_number=reven + i * 1000,
            )
            for i, a in enumerate(Revenues_Income)
        ]
        Charts_of_account.objects.bulk_create(Revenues)
        print("Company Accounts Revenues created")

        EXPENSES = (
            "Regular Expense",  # Debit
            'Freight Expense',  # Debit
            "Interest Expense",  # Debit
            "Tax Expense",  # Debit
            "Capital Expense",  # Debit
            "Depreciation Expense",  # Debit
            "Amortization Expense",  # Debit
            "Other Expense",  # Debit
            "Marketing Expenses",  # Debit
            "Payroll Expenses",  # Debit
            "Cost of Goods Sold",  # Debit
        )
        expense = 50100000
        Expenses = [
            Charts_of_account(
                account_type="Expenses",
                account_balance_type="Debit",
                # slug=slugify(str(a)),
                name=str(a),
                acc_number=expense + i * 2000,
            )
            for i, a in enumerate(EXPENSES)
        ]
        Charts_of_account.objects.bulk_create(Expenses)
        print("Company Accounts Expenses created")

    if created:

        roles=pd.read_excel('./testdummy/ISCO-08 EN Structure and definitions.xlsx',sheet_name='ISCO-08 EN Struct and defin')
        
        for index, row in roles.drop_duplicates().iterrows():
            oc,created=Occupation.objects.update_or_create(
                name=row["Title EN"].capitalize(),
                defaults={
                    "definition": row["Definition"],
                    "task": row["Tasks include"],
                }
            )

                


```

```python

from django.db import models
from djmoney.money import Money
from addons.models import createdtimestamp_uid,activearchlockedMixin
# Create your models here.
from django.urls import reverse

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from party.models import Staff, Occupation,User
from department.models import Department,Branch,Shift
from contact.models import Phone, Address, Email, Website,Country #,Document
from accounts.models import Tax,Bank,Account,calculate_tax_amount

from django.contrib.postgres.fields import ArrayField
from department.models import Room
from djmoney.models.fields import MoneyField,CurrencyField
from accounts.models import default_currency,allowed_currencies
# from djmoney.models.fields import MoneyField, CurrencyField
# the hrm models will contain models related to human resource management such as employee, department, attendance, leave, payroll, etc.
# These models will help in managing employee records, tracking attendance, processing payroll, and handling leave requests.
# The models will also facilitate performance evaluations and training management for employees.
# The hrm models will be integrated with other modules like sales to ensure seamless operations across the organization.
# https://medium.com/@chideraozigbo/database-design-i-employee-attrition-management-system-25d89503c08b
# https://deepwiki.com/fellow-me/hrm/4-database-design
# department management here


# import timezone
from django.utils import timezone

# https://deepwiki.com/fellow-me/hrm/4-database-design
# https://www.geeksforgeeks.org/sql/how-to-design-er-diagrams-for-human-resource-management-hrm-systems/
# https://www.ukessays.com/essays/computer-science/logical-database-design-hr-management-6214.php
# https://deepwiki.com/aureuserp/aureuserp/10-hr-and-time-management
# schedule shifts for employees 
# shift model to define different shifts for employees
# Scheduled shifts for employees informs attendance tracking

class Skill(createdtimestamp_uid):
    name = models.CharField(_("Skill Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    skillset = models.ManyToManyField("self", verbose_name=_("Skill Sets"), blank=True)
    # consider either associating skills with occupations or roles

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        return reverse("Skill_detail", kwargs={"pk": self.pk})

class Holiday(createdtimestamp_uid, activearchlockedMixin):
    name = models.CharField(_("Holiday Name"), max_length=100,)
    date = models.DateField(_("Holiday Date"))
    is_public = models.BooleanField(_("Is Public Holiday?"), default=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    is_recurring = models.BooleanField(_("Is Recurring"), default=False)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True, related_name='holidays')

    class Meta:
        verbose_name = _("Holiday")
        verbose_name_plural = _("Holidays")
        unique_together = ('name', 'date',)

    def __str__(self):
        return f"{self.name} on {self.date}"

    def get_absolute_url(self):
        return reverse("Holiday_detail", kwargs={"pk": self.pk})


# meeting subjects are specific topics or agendas for meetings
purpose_choices=(
    # ('team_meeting','team_meeting'),
    # ('project_update','project_update'),
    # ('client_meeting','client_meeting'),
    # ('training_session','training_session'),
    # ('performance_review','performance_review'),
    # ('strategic_planning','strategic_planning'),
    # ('brainstorming_session','brainstorming_session'),
    # ('problem_solving','problem_solving'),
    # ('decision_making','decision_making'),
    # ('status_report','status_report'),
            ('Project Discussion', 'Project Discussion'),
            ('Budget Meeting', 'Budget Meeting'),
           ('Strategy Session', 'Strategy Session'),
            ('Performance Review', 'Performance Review'),
            ('Training Session', 'Training Session'),
            ('Client Meeting', 'Client Meeting'),
            ('Team Building', 'Team Building'),
            ('Interview', 'Interview'),
            ('Workshop', 'Workshop'),
            ('Seminar', 'Seminar'),
           ('Board Meeting', 'Board Meeting'),
           ('Sales Meeting', 'Sales Meeting'),
           ('Planning Meeting', 'Planning Meeting'),
            ('Brainstorming Session', 'Brainstorming Session'),
            ('Presentation', 'Presentation'),
)

# 
class MeetingSubject(createdtimestamp_uid):
    purpose_type = ArrayField(
        models.CharField(max_length=100, choices=purpose_choices),
        verbose_name=_("Activities"),
        blank=True,
        default=list,
    )
    subject = models.CharField(_("Subject"), max_length=200, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    staff=models.ForeignKey(Staff, verbose_name=_("Staff"), on_delete=models.PROTECT,)

    class Meta:
        verbose_name = _("Meeting Subject")
        verbose_name_plural = _("Meeting Subjects")

    def __str__(self):
        return self.subject

    def get_absolute_url(self):
        return reverse("MeetingSubject_detail", kwargs={"pk": self.pk})



class Meeting(createdtimestamp_uid):
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='scheduled_meetings')
    subject = models.ForeignKey(MeetingSubject, on_delete=models.PROTECT, related_name='scheduled_meetings')
    date= models.DateField(_("Scheduled Date"))
    start_time = models.TimeField(_("Scheduled Start Time"))
    end_time = models.TimeField(_("Scheduled End Time"))
    actual_date = models.DateField(_("Actual Date"), blank=True, null=True)
    actual_start_time = models.TimeField(_("Actual Start Time"), blank=True, null=True)
    actual_end_time = models.TimeField(_("Actual End Time"), blank=True, null=True)
    assigned_branch = models.ManyToManyField(Branch, verbose_name=_("Assigned Branch"), blank=True,)
    assigned_department= models.ManyToManyField(Department, verbose_name=_("Assigned Department"), blank=True,)
    staff=models.ForeignKey(Staff, verbose_name=_("Staff"), on_delete=models.PROTECT,)
    attendees = models.ManyToManyField(User, verbose_name=_("Attendees"), blank=True, related_name='meetings_attended')
    # scheduled_by = models.ManyToManyField(Staff, verbose_name=_("Scheduled By"), blank=True, related_name='scheduled_meetings_created')
    participants = models.ManyToManyField(User, verbose_name=_("Invited Participants"), blank=True, related_name='scheduled_meetings')
    # participants can be staff, suppliers,or customers  
    notes = models.TextField(_("Notes"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        # ('scheduled', 'Scheduled'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'), #meeting is ongoing
        ('completed', 'Completed'), #meeting has ended and all action items are done
        ('canceled', 'Canceled'),
        ('rescheduled', 'Rescheduled'),
    ], default='pending')
    rescheduled_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='rescheduled_meetings')
    agenda = ArrayField(
        models.CharField(max_length=200),
        verbose_name=_("Agenda"),
        blank=True,
        default=list,
    )
    action_items = ArrayField(
        models.CharField(max_length=200),
        verbose_name=_("Action Items"),
        blank=True,
        default=list,
    )
    minutes = models.TextField(_("Minutes"), blank=True, null=True)

    ajourned = models.BooleanField(_("Adjourned?"), default=False)
    follow_up_date = models.DateTimeField(_("Follow Up Date"), blank=True, null=True)

    class Meta:
        verbose_name = _("Meeting")
        verbose_name_plural = _("Meetings")
        unique_together=('subject', 'date', 'start_time',)

    def __str__(self):
        return f"{self.subject.subject} in {self.room.name} from {self.start_time} to {self.end_time}"

    def get_absolute_url(self):
        return reverse("Meeting_detail", kwargs={"pk": self.pk})


class Vacancy(createdtimestamp_uid, activearchlockedMixin):
    title = models.CharField(_("Job Title"), max_length=100)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='vacancies')
    description = models.TextField(_("Job Description"))
    requirements = models.TextField(_("Job Requirements"))
    posted_date = models.DateField(_("Posted Date"), auto_now_add=True)
    closing_date = models.DateField(_("Closing Date"))
    # is_active = models.BooleanField(_("Is Active"), default=True)
    is_filled = models.BooleanField(_("Is Filled"), default=False)
    # applicants can be modelled in recruitment app

    class Meta:
        verbose_name = _("Vacancy")
        verbose_name_plural = _("Vacancies")

    def get_absolute_url(self):
        return reverse("Vacancy_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.title} - {self.department.name}"



# Deductions include agreed upon amounts to be subtracted from an employee's salary, such as taxes, insurance premiums, retirement contributions, and other voluntary or involuntary deductions.
class Deduction(createdtimestamp_uid,activearchlockedMixin):

    # lists of deductions that can be applied to employee salaries
    name = models.CharField(_("Deduction Name"), max_length=100,)
    description = models.TextField(_("Description"), blank=True, null=True)

    deductionratetype=(
        ('percent','percent'),
        ('fixed','fixed')
                  )

    deduction_types=(
        # ('tax', 'Tax'),
        ('insurance', 'Insurance'),
        ('social_security', 'Social Security'),
        ('investment', 'Investment'),
        ('retirement', 'Retirement Contribution'),
        # ('loan_repayment', 'Loan Repayment'),
        # ('other', 'Other'),4
    )

    frequencytype=(
        ('on_transaction','on_transaction'),
        ('weekly','weekly'),
        ('biweekly','biweekly'),
        ('monthly','monthly'),
        ('quarterly','quarterly'),
        ('annually','annually')
    )
    frequency = models.CharField(
        _("Frequency"), choices=frequencytype, max_length=20,default='monthly'
    )
    
    deduction_rate_type = models.CharField(
        _("Rate Type"), choices=deductionratetype, max_length=20,default='percent'
    )
    deduction_type = models.CharField(
        _("Deduction Type"), choices=deduction_types, max_length=30,default='social_security'
    )
    # deduct
    # caps minimum and maximum deduction amounts for each deduction type to prevent excessive deductions from employee salaries
    deduction = models.DecimalField(
        _("Deduction"), max_digits=20, decimal_places=4, default=0
    )
    # is_tax_deductable = models.BooleanField(_("Is Tax Deduction?"), default=False)
    currency=CurrencyField(default=default_currency, choices=[(cur, cur) for cur in allowed_currencies])
    min_deduction_amount = MoneyField(
        _("Minimum Deduction Amount"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies],  null=True, blank=True 
    )
    max_deduction_amount = MoneyField(
        _("Maximum Deduction Amount"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies], null=True, blank=True 
    )

    # ensure that if deduction rate type is percent, the deduction field value must be between 0 and 100 and if deduction rate type is fixed, the deduction field value must be greater than or equal to 0 and less than or equal to the maximum deduction amount for that deduction type
    # ensure that if deduction type is tax, the deduction field value must be less than or equal to 50% of the employee's gross salary and if deduction type is insurance, the deduction field value must be less than or equal to 30% of the employee's gross salary and if deduction type is retirement contribution, the deduction field value must be less than or equal to 20% of the employee's gross salary and if deduction type is loan repayment, the deduction field value must be less than or equal to 40% of the employee's gross salary
    # ensure that the account associated with the deduction is valid and active in the accounting app to prevent errors during payroll processing and to ensure accurate financial reporting of total deductions for each type of deduction and corresponds to the type of deduction being applied to employee salaries and to facilitate proper tracking and reconciliation of deductions in the accounting app
    # if 
    # each deduction has an associated account in the accounting app to track the total deductions made for each type of deduction
    # account = models.CharField(_("Account"), max_length=100, blank=True, null=True)
    # if deduction is percent, the deduction field represents the percentage to be deducted from the salary
    # if deduction is amount, the deduction field represents the fixed amount to be deducted from the salary
    # deductions have a frequency of application: monthly, quarterly, annually,.
    # deductions are essentially for other statutory deductions like social security, health insurance, etc. besides taxes which are already modelled in the tax model in accounts app
    class Meta:
        verbose_name = _("Deduction")
        verbose_name_plural = _("Deductions")
        unique_together = ('name', 'currency',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Deduction_detail", kwargs={"pk": self.pk})

    def clean(self):
        if not self.deduction_rate_type == 'percent' and self.currency is None:
            raise ValidationError(_("Currency must be specified for fixed amount deductions."))
        if self.deduction_rate_type == 'percent' and (self.deduction < 0 or self.deduction > 100):
            raise ValidationError(_("Deduction percentage must be between 0 and 100."))
        if self.deduction_rate_type == 'fixed' and self.deduction < 0:
            raise ValidationError(_("Deduction amount must be greater than or equal to 0."))
        if self.max_deduction_amount and self.deduction > self.max_deduction_amount.amount:
            raise ValidationError(_("Deduction amount cannot exceed the maximum deduction amount for this deduction type."))
        return super().clean()

class Benefit(createdtimestamp_uid,activearchlockedMixin):
    name = models.CharField(_("Benefit Name"), max_length=100, )
    # benefit types include health insurance, retirement plans, paid time off, etc. and each benefit type has specific criteria for eligibility and calculation of the benefit amount to ensure fairness and consistency in the application of benefits across the organization and to motivate employees to meet specific performance or attendance targets and to encourage employee referrals.
    description = models.TextField(_("Description"), blank=True, null=True)

    benefit_rate_type_choices=(
        ('percent','percent'),
        ('fixed','fixed')
    )

    benefit_rate_type = models.CharField(
        _("Benefit Rate Type"), max_length=10, choices=benefit_rate_type_choices, default='fixed'
    )
    frequencytype=(
        ('on_transaction','on_transaction'),
        ('weekly','weekly'),
        ('biweekly','biweekly'),
        ('monthly','monthly'),
        ('quarterly','quarterly'),
        ('annually','annually')
    )
    is_tax_deductable = models.BooleanField(_("Is Tax Deduction?"), default=False)

    frequency = models.CharField(
        _("Frequency"), choices=frequencytype, max_length=20,default='monthly'
    )
    benefit = models.DecimalField(
        _("Benefit"), max_digits=20, decimal_places=4, default=0
    )
    currency=CurrencyField(default=default_currency, choices=[(cur, cur) for cur in allowed_currencies])
    min_benefit_amount = MoneyField(
        _("Minimum Benefit Amount"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies],  null=True, blank=True 
    )
    max_benefit_amount = MoneyField(
        _("Maximum Benefit Amount"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies], null=True, blank=True 
    )

    class Meta:
        verbose_name = _("Benefit")
        verbose_name_plural = _("Benefits")
        unique_together = ('name', 'currency',)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse("Benefit_detail", kwargs={"pk": self.pk})
    


# Employee management rule model 
class EmployeeManagementRule(createdtimestamp_uid):
    name = models.CharField(_("Rule Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    # defines the rules for both rewards and punishments
    #

    # leave_carry_forward = models.BooleanField(_("Carry Forward"), default=False) # if carry forward is true, the unused leave days will be carried forward to the next year and added to the employee's leave balance for that year to allow employees to utilize their allocated leave days effectively and to encourage work-life balance and employee well-being.
    # staffloansallowed = models.BooleanField(_("Staff Loans Allowed?"), default=False) # if staff loans allowed is true, employees can apply for loans from the organization and the employee management rules will define the criteria for loan eligibility, maximum loan amounts, repayment terms, and interest rates to ensure responsible lending practices and to support employees in times of financial need while maintaining the financial stability of the organization.


    # rule_type = models.CharField(_("Rule Type"), max_length=50, choices=[
    #     ('attendance', 'Attendance Rule'),
    #     ('leave', 'Leave Rule'),
    #     ('performance_evaluation', 'Performance Evaluation Rule'),
    #     ('other', 'Other Rule'),
    # ], default='other')

    class Meta:
        verbose_name = _("Employee Management Rule")
        verbose_name_plural = _("Employee Management Rules")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("EmployeeManagementRule_detail", kwargs={"pk": self.pk})

class EmployeeManagement(createdtimestamp_uid):
    id=None
    is_employed=models.BooleanField(_("Employed?"), default=True)    
    works_weekends = models.BooleanField(_("Works Weekends?"), default=True) # if works weekends is true, the employee is expected to work on weekends and the employee management rules will define the criteria for weekend work, including any additional compensation or benefits for working on weekends to ensure fair treatment of employees and to maintain a positive work environment.
    staff =models.OneToOneField(Staff, verbose_name=_("Staff"), on_delete=models.CASCADE,primary_key=True, related_name='employee_management')
    position = models.ForeignKey(Occupation, on_delete=models.SET_NULL, null=True, blank=True)
    date_hired = models.DateField(_("Date Hired"),null=True, blank=True)
    date_terminated = models.DateField(_("Date Terminated"), null=True, blank=True)
    leave_days_allocated=models.PositiveIntegerField(_("Leave Days Allocated"), default=0)
    # gross_salary = MoneyField(_("Gross Salary"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies], null=True, blank=True)
    taxes=models.ManyToManyField(Tax, verbose_name=_("Taxes"), blank=True)
    # salary_tax=MoneyField(_("Salary Tax"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies], null=True, blank=True)
    net_salary = MoneyField(_("Net Salary"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies], null=True, blank=True)
    overtime_rate=MoneyField(_("Overtime Rate/Hour"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies], null=True, blank=True)
    salary_rate_period = models.CharField('Salary Rate Period', max_length=50, choices=[
        ('monthly', 'Monthly'),
        ('biweekly', 'Biweekly'),
        ('weekly', 'Weekly'),
        ('daily', 'Daily'),
        ('hourly', 'Hourly'),
    ], default='monthly') 
    weekend_days_salary_rate=MoneyField(_("Weekend Days Salary Rate/Day"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies], null=True, blank=True)
    maximum_overtime_hours_per_session=models.IntegerField(_("Maximum Overtime Hours/Day"), default=0)
    preferred_payment_method = models.CharField(_("Preferred Payment Method"), max_length=100, choices=[
        ('bank_transfer', _("Bank Transfer")),
        ('cheque', _("Cheque")),
        ('cash', _("Cash")),
        ('mobile_money', _("Mobile Money")),
    ], default='bank_transfer', editable=False)
    last_payment_date = models.DateField(_("Last Payment Date"), blank=True, null=True)
    # vacancy can be linked to employee management to track which employee is hired for which vacancy and to easily retrieve the job description and requirements for each employee
    vacancy = models.ForeignKey(Vacancy, on_delete=models.SET_NULL, null=True, blank=True, related_name='employees')
    

    class Meta:
        verbose_name = _("Employee Management")
        verbose_name_plural = _("Employee Managements")
        
    def __str__(self):
        return self.staff.staff.get_full_name()
    

    def get_absolute_url(self):
        return reverse("EmployeeManagement_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if self._state.adding and not self.date_hired and self.is_employed:
             self.date_hired = timezone.now().date()
        # if not self.date_hired:
        #     self.date_hired = timezone.now().date()
        if not self.is_employed:
            self.date_terminated = timezone.now().date()
        if self.is_employed and self.date_terminated:
            self.date_terminated = None
                

        
        super().save(*args, **kwargs)


# model for employee salary rules to define the rules for calculating employee salaries based on factors such as job position, experience, performance, and other relevant criteria to ensure fair and consistent compensation practices across the organization and to motivate employees to perform at their best and to retain top talent in the organization.
# this model can include fields such as rule name, description, criteria for salary calculation, and the corresponding salary amount or percentage to be applied based on the defined criteria and this allows for transparent and objective salary determination for employees and facilitates payroll processing and financial planning for both employees and the organization.
# this model is linked to the employee management model to apply the salary rules to individual employees based on their job position, experience, performance, and other relevant criteria and to ensure accurate calculation of employee salaries and to facilitate payroll processing and financial planning for both employees and the organization.
# it also includes rules for employee rewards and punishments to define the criteria and corresponding rewards or penalties for employee performance, attendance, or other relevant factors to motivate employees to perform at their best and to maintain a positive work environment and to ensure fair and consistent application of rewards and punishments across the organization.

class EmployeeSalaryRule(createdtimestamp_uid):
    employee=models.OneToOneField(EmployeeManagement, on_delete=models.CASCADE, verbose_name=_("Employee"), related_name='salary_rule')
    # rules for when a 

# model for employee severance package to track the details of the severance package offered to employees upon termination of employment and to ensure compliance with labor laws and company policies regarding severance pay and to facilitate accurate financial planning and reporting for both employees and the organization.

class EmployeeSeverancePackage(createdtimestamp_uid):
    employee=models.OneToOneField(EmployeeManagement, on_delete=models.CASCADE, verbose_name=_("Employee"), related_name='severance_package')
    # severance_amount = MoneyField(_("Severance Amount"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies], null=True, blank=True)
    # payment_schedule = models.CharField(_("Payment Schedule"), max_length=100, blank=True, null=True)
    # additional_benefits = models.TextField(_("Additional Benefits"), blank=True, null=True)
    # notes = models.TextField(_("Notes"), blank=True, null=True)

class Employee_Deduction(createdtimestamp_uid):
    # automatically set as archived when the end date is reached and recurring is false to prevent deductions from being applied to employee salaries after the end date and to ensure accurate financial reporting of total deductions for each employee and to facilitate payroll processing and financial planning for both employees and the organization.

    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE,verbose_name=_("Employee"),related_name='deductions')
    deduction = models.ForeignKey(Deduction, on_delete=models.CASCADE,verbose_name=_("Deduction"),)
    # amount = MoneyField(_("Estimated Deduction Amount/Time interval"), max_digits=20, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies], null=True, blank=True, editable=False)
    end_date = models.DateField(_("End Date"), blank=True, null=True)
    recurring = models.BooleanField(_("Recurring?"), default=False) #if recurring is true, the deduction will be applied to the employee's salary until the end date is reached and the amount field represents the estimated deduction amount for each time interval based on the frequency of the deduction and the employee's gross salary if the deduction rate type is percent or the fixed amount if the deduction rate type is fixed and this allows for accurate estimation of total deductions for each employee and facilitates payroll processing and financial planning for both employees and the organization.
    account=models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='deductions',editable=False,limit_choices_to={"accounttype__name": "Other Liabilities"})

    class Meta:
        verbose_name = _("Employee_Deduction")
        verbose_name_plural = _("Employee_Deductions")
        unique_together = ('employee', 'deduction',)

    def __str__(self):
        return f"{self.employee.staff.staff.get_full_name()} - {self.deduction.name}"

    def get_absolute_url(self):
        return reverse("Employee_Deduction_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        # automatically calculate the estimated deduction amount based on the deduction rate type and the employee's gross salary if the deduction rate type is percent or the fixed amount if the deduction rate type is fixed and save it to the amount field to ensure accurate estimation of total deductions for each employee and to facilitate payroll processing and financial planning for both employees and the organization.
        # if self.deduction.deduction_rate_type == 'percent' and self.employee.gross_salary:
        #     self.amount = (self.deduction.deduction) * self.employee.gross_salary
        #     # ensure that if self.amount exceeds the maximum deduction amount for that deduction type, set the amount to the maximum deduction amount to prevent excessive deductions from employee salaries and to ensure accurate financial reporting of total deductions for each type of deduction and to facilitate payroll processing and financial planning for both employees and the organization. 
        #     if self.deduction.max_deduction_amount and self.amount.amount > self.deduction.max_deduction_amount.amount:
        #         self.amount = self.deduction.max_deduction_amount.amount
            
        # elif self.deduction.deduction_rate_type == 'fixed':
        #         self.amount = Money(self.deduction.deduction, self.deduction.currency   )
        super().save(*args, **kwargs)

    @property
    def amount(self):
        if self.deduction.deduction_rate_type == 'percent' and self.employee.net_salary:
            calculated_amount = (self.deduction.deduction) * self.employee.net_salary.amount
            if self.deduction.max_deduction_amount and self.deduction.max_deduction_amount.amount>0 and calculated_amount > self.deduction.max_deduction_amount.amount:
                return self.deduction.max_deduction_amount.amount
            if self.deduction.min_deduction_amount and self.deduction.min_deduction_amount.amount>0 and  calculated_amount < self.deduction.min_deduction_amount.amount:
                return self.deduction.min_deduction_amount.amount
            return Money(calculated_amount, self.deduction.currency).amount
        elif self.deduction.deduction_rate_type == 'fixed':
            return Money(self.deduction.deduction, self.deduction.currency).amount
        return None


class Employee_Benefit(createdtimestamp_uid):
    # automatically set as archived when the end date is reached and recurring is false to prevent benefits from being applied to employee salaries after the end date and to ensure accurate financial reporting of total benefits for each employee and to facilitate payroll processing and financial planning for both employees and the organization.
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE,verbose_name=_("Employee"),related_name='benefits')
    benefit = models.ForeignKey(Benefit, on_delete=models.CASCADE,verbose_name=_("Benefit"),)
    # amount = MoneyField(_("Estimated Benefit Amount/Time interval"), max_digits=20, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies], null=True, blank=True, editable=False)  
    end_date = models.DateField(_("End Date"), blank=True, null=True)
    recurring = models.BooleanField(_("Recurring?"), default=False) #if recurring is true, the benefit will be applied to the employee's salary until the end date is reached and the amount field represents the estimated benefit amount for each time interval based on the frequency of the benefit and the employee's gross salary if the benefit rate type is percent or the fixed amount if the benefit rate type is fixed and this allows for accurate estimation of total benefits for each employee and facilitates payroll processing and financial planning for both employees and the organization.
    # account=models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='benefits',editable=False,limit_choices_to={"accounttype__name": "Expenses"})
    # benefit account is essentially an expense account in the accounting app to track the total benefits given to employees and to facilitate proper tracking and reconciliation of benefits in the accounting app and to ensure accurate financial reporting of total benefits for each type of benefit and corresponds to the type of benefit being applied to employee salaries.
    class Meta:
        verbose_name = _("Employee_Benefit")
        verbose_name_plural = _("Employee_Benefits")
        unique_together = ('employee', 'benefit',)

    def __str__(self):
        return f"{self.employee.staff.staff.get_full_name()} - {self.benefit.name}"

    def get_absolute_url(self):
        return reverse("Employee_Benefit_detail", kwargs={"pk": self.pk})
    
    def save(self, *args, **kwargs):
        # automatically calculate the estimated benefit amount based on the benefit rate type and the employee's gross salary if the benefit rate type is percent or the fixed amount if the benefit rate type is fixed and save it to the amount field to ensure accurate estimation of total benefits for each employee and to facilitate payroll processing and financial planning for both employees and the organization.
        # if self.benefit.benefit_rate_type == 'percent' and self.employee.gross_salary:
        #     self.amount = (self.benefit.benefit) * self.employee.gross_salary
        #     # ensure that if self.amount exceeds the maximum benefit amount for that benefit type, set the amount to the maximum benefit amount to prevent excessive benefits from being applied to employee salaries and to ensure accurate financial reporting of total benefits for each type of benefit and to facilitate payroll processing and financial planning for both employees and the organization. 
        #     if self.benefit.max_benefit_amount and self.amount.amount > self.benefit.max_benefit_amount.amount:
        #         self.amount = self.benefit.max_benefit_amount
            
        # elif self.benefit.benefit_rate_type == 'fixed':
        #         self.amount = Money(self.benefit.benefit, self.benefit.currency   )
        super().save(*args, **kwargs)


    @property
    def amount(self):
        if self.benefit.benefit_rate_type == 'percent' and self.employee.net_salary:
            calculated_amount = (self.benefit.benefit) * self.employee.net_salary.amount
            if self.benefit.max_benefit_amount and self.benefit.max_benefit_amount.amount>0 and calculated_amount > self.benefit.max_benefit_amount.amount:
                return self.benefit.max_benefit_amount.amount
            if self.benefit.min_benefit_amount and self.benefit.min_benefit_amount.amount>0 and  calculated_amount < self.benefit.min_benefit_amount.amount:
                return self.benefit.min_benefit_amount.amount
            return Money(calculated_amount, self.benefit.currency).amount
        elif self.benefit.benefit_rate_type == 'fixed':
            return Money(self.benefit.benefit, self.benefit.currency).amount
        return None


class Certification(createdtimestamp_uid):
    name = models.CharField(_("Certification"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)

    class Meta:
        verbose_name = _("Certification")
        verbose_name_plural = _("Certifications")

    def __str__(self):
        return self.name

class EmployeeSkill(createdtimestamp_uid):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE,)
    proficiency_level = models.CharField(_("Proficiency Level"), max_length=30, choices=[
        ('beginner', _("Beginner")),
        ('intermediate', _("Intermediate")),
        ('advanced', _("Advanced")),
        ('expert', _("Expert")),
    ], default='beginner')
    years_of_experience = models.IntegerField(_("Years of Experience"), default=0)
    # last_used = models.DateField(_("Last Used"), blank=True, null=True)
    # endorsements = models.IntegerField(_("Endorsements"), default=0)
    # skills=models.ManyToManyField(Skill, verbose_name=_("Skills"), blank=True)
    skill=models.ForeignKey(Skill, verbose_name=_("Skills"), on_delete=models.PROTECT, related_name='employee_skills')
    certificates = models.ManyToManyField(Certification, verbose_name=_("Certificates"), blank=True)
    class Meta:
        verbose_name = _("Employee Skill")
        verbose_name_plural = _("Employee Skills")
        unique_together = ('employee', 'skill',)

    def __str__(self):
        return f"{self.employee.staff.user.get_full_name()} - {self.skill.name} ({self.proficiency_level})"
    
    def get_absolute_url(self): 
        return reverse("EmployeeSkill_detail", kwargs={"pk": self.pk})



class EmployeeBankDetails(createdtimestamp_uid):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name='bank_details')
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='employee_bank_details')
    account_number = models.CharField(_("Account Number"), max_length=50)
    account_name = models.CharField(_("Account Name"), max_length=100)
    swift_code = models.CharField(_("SWIFT Code"), max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = _("Employee Bank Detail")
        verbose_name_plural = _("Employee Bank Details")
        unique_together = ('employee', 'bank', 'account_number',)

    def __str__(self):
        return f"{self.employee.staff.user.get_full_name()} - {self.bank.name} ({self.account_number})"

class DocumentType(createdtimestamp_uid):
    name = models.CharField(_("Document Type"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)

    class Meta:
        verbose_name = _("Document Type")
        verbose_name_plural = _("Document Types")

    def __str__(self):
        return self.name


class Document(createdtimestamp_uid):
    name = models.CharField(_("Document Name"), max_length=200)
    file = models.FileField(_("File"), upload_to='employee_documents/')
    uploaded_at = models.DateTimeField(_("Uploaded At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    def __str__(self):
        return self.name


class EmployeeDocument(createdtimestamp_uid):
    document_type = models.ForeignKey(DocumentType, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_documents')
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name='employee_documents')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='employee_documents')
    description = models.TextField(_("Description"), blank=True, null=True)

    class Meta:
        verbose_name = _("Employee Document")
        verbose_name_plural = _("Employee Documents")

    def __str__(self):
        return f"{self.employee.staff.user.get_full_name()} - {self.document.name}"


class LeaveType(createdtimestamp_uid, activearchlockedMixin):

    
    name = models.CharField(_("Leave Type"), max_length=50, )
    description = models.TextField(_("Description"), blank=True, null=True)    
    # examples: sick leave, vacation leave, maternity leave, paternity leave, etc.
    is_paid = models.BooleanField(_("Is Paid"), default=True)
    # if is paid is true, the leave days will be deducted from the employee's leave balance
    # requires_approval = models.BooleanField(_("Requires Approval"), default=True)
    approval_by = models.ManyToManyField(Staff, blank=True, related_name='approved_by_leave_types')
    rollover_allowed = models.BooleanField(_("Yearly Rollover Allowed"), default=False)
    requires_medical_certificate = models.BooleanField(_("Requires Medical Certificate"), default=False)
    requires_notice_days = models.PositiveIntegerField(_("Requires Notice Days"), default=0)
    required_hr_approval = models.BooleanField(_("Requires HR Approval"), default=False)
    department = models.ForeignKey(
        Department,
        verbose_name=_("Department"),
        on_delete=models.PROTECT,
    )

    max_days_allowed = models.IntegerField(_("Max Days Allowed"), default=0)
    # status = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        verbose_name = _("Leave Type")
        verbose_name_plural = _("Leave Types")
        unique_together = ('department', 'name',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Leavetype_detail", kwargs={"pk": self.pk})



# leave requests
class Leave(createdtimestamp_uid):
    staff = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name='staff_leave')
    requested_days= models.IntegerField(_("Requested Days"), default=1)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name='leave_requests')
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    days= models.IntegerField(_("Days"), default=0, editable=False)
    reason = models.TextField(_("Reason"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    approved_rejected_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leave_requests')
    # 

    class Meta:
        verbose_name = _("Leave Request")
        verbose_name_plural = _("Leave Requests")

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.start_date} to {self.end_date}"
    
    def save(self, *args, **kwargs):
        # automatically calculate the number of days for the leave request based on the start date and end date to ensure accurate tracking of leave days and to facilitate leave management and planning for both employees and the organization.
        if self.start_date and self.end_date:
            self.days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)


# skipped
class ScheduledShifts(createdtimestamp_uid):
    holiday = models.ForeignKey(Holiday, on_delete=models.SET_NULL, null=True, blank=True, related_name='scheduled_shifts')
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name='staff_scheduled')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, null=True, blank=True, related_name='scheduled_shifts')
    branch= models.ForeignKey(Branch, on_delete=models.CASCADE,)
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    notes = models.TextField(_("Notes"), blank=True, null=True)
    additional_info = models.JSONField(blank=True, null=True, default=dict)
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name='scheduled_shifts_created')
    is_onleave= models.BooleanField(_("Is On Leave?"), default=False)
    leave= models.ForeignKey(Leave, on_delete=models.SET_NULL, null=True, blank=True, related_name='scheduled_shifts',limit_choices_to={'status': 'approved'})
    class Meta:
        verbose_name = _("Scheduled Shift")
        verbose_name_plural = _("Scheduled Shifts")
        # unique_together = ('employee', 'branch', 'shift', 'start_date', 'end_date',)

    def __str__(self):
        return f"{self.employee.staff.user.get_full_name()} - {self.shift.name} from {self.start_date} to {self.end_date}"
    # raise validation error if the employee is on leave and leave is null
    def clean(self):
        if self.is_onleave and not self.leave:
            raise ValidationError(_("Leave request must be provided if the employee is on leave."))
        if self.leave and not self.is_onleave:
            raise ValidationError(_("Is On Leave must be true if a leave request is provided."))
        return super().clean() 

    def get_absolute_url(self):
        return reverse("ScheduledShift_detail", kwargs={"pk": self.pk})

    # def save(self, *args, **kwargs):
    #     # automatically set is_onleave based on whether a leave request is associated with the scheduled shift
    #     if self.leave and self.leave.status == 'approved':
    #         self.is_onleave = True
    #     else:
    #         self.is_onleave = False
    #     super().save(*args, **kwargs)


class Attendance(createdtimestamp_uid):

    scheduled_shift= models.ForeignKey(ScheduledShifts, on_delete=models.CASCADE,  null=True, blank=True)
    employee= models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE,related_name='attendances')
    branch= models.ForeignKey(Branch, on_delete=models.CASCADE,)
    date = models.DateField(_("Date"), auto_now_add=True)
    check_in = models.TimeField(_("Check In"), )
    check_out = models.TimeField(_("Check Out"), null=True, blank=True)
    break_start = models.TimeField(_("Break Start"), null=True, blank=True)
    break_end = models.TimeField(_("Break End"), null=True, blank=True)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ("present", _("Present")),
        ("absent", _("Absent")),
        ("late", _("Late")),
        ("excused", _("Excused")),
    ], default="present")


# overtime is requested when an employee works beyond their scheduled shift hours

    class Meta:
        verbose_name = _("Attendance")
        verbose_name_plural = _("Attendances")

    def __str__(self):
        return self.employee.staff.user.get_full_name()

    def get_absolute_url(self):
        return reverse("Attendance_detail", kwargs={"pk": self.pk})





class OverTime(createdtimestamp_uid):
    # request=models.OneToOneField(OvertimeRequest, on_delete=models.CASCADE, related_name='overtimes',limit_choices_to={'status': 'approved'})
    attendance=models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='overtime')
    requested_hours = models.IntegerField(_("Hours"), default=0)
    planned_activities = ArrayField(
        models.CharField(max_length=200),
        verbose_name=_("Agenda"),
        blank=True,
        default=list,
    )
    # approved byy and
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
        ('rejected', 'Rejected'),
    ], default='pending')
    requested_by = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name='requested_overtime_requests')
    approved_rejected_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_overtime_requests')
    requested_start_time = models.TimeField(_("Requested At"), auto_now_add=True)
    requested_end_time = models.TimeField(_("Requested End At"), null=True, blank=True)
    # date = models.DateField(_("Date"))
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    total_hours = models.IntegerField(_("Total Hours"))
    # total_hours = models.DecimalField(_("Total Hours"), max_digits=5, decimal_places=2)
    # rate_per_hour = MoneyField(_("Rate Per Hour"), max_digits=10, decimal_places=2, default_currency='USD')
    # total_amount = MoneyField(_("Total Amount"), max_digits=10, decimal_places=2, default_currency='USD')
    # records the actual overtime, Time it commenced and ended, total hours worked, rate applied, total amount payable
    # employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name='overtimes')
    # additional_info = models.JSONField(blank=True, null=True, default=dict)
    est_overtime_amount = MoneyField(_("Overtime Amount"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies], null=True, blank=True)


    class Meta:
        verbose_name = _("OverTime")
        verbose_name_plural = _("OverTimes")

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # calculate total hours
        if self.end_time and self.start_time:
            from datetime import datetime, date
            time_difference = datetime.combine(date.min, self.end_time) - datetime.combine(date.min, self.start_time)
            self.total_hours = time_difference.seconds // 3600
            # calculate total amount
            if self.total_hours:
                self.overtime_amount = self.total_hours * self.employee.overtime_rate if self.employee.maximum_overtime_hours >= self.total_hours else self.employee.overtime_rate * self.employee.maximum_overtime_hours
                # self.overtime_amount = self.total_hours * self.employee.overtime_rate

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("OverTime_detail", kwargs={"pk": self.pk})









# tasks and activities can be modelled using the tasks model from crm app

# 

# employee task assignments can be modelled using the tasks model from crm app


# employee todo lists can be modelled using the tasks model from crm app

# employee teams can be modelled using the department app
# attendance model to track employee attendance, check-in and check-out times, etc.


# payroll model to manage employee salaries, deductions, bonuses, etc.  
# the payroll model creates a request for payment for a given period
# the payroll model will be linked the transaction model in the accounting app to record the payment made to the employee
# with a pending status until the payment is processed and when confirmed the transaction model will also generate payslips for employees and deduct taxes and other statutory deductions and account for them in the accounting app
# the payroll model will also track any bonuses or deductions applied to the employee's salary
# the payroll model will also generate reports for payroll summaries, tax filings, and other statutory requirements and all statutory deductions will be linked to the accounting app for proper tracking and reporting

# StaffLoans records the loans taken by employees from the organization, # including loan amount, interest rate, repayment schedule, and outstanding balance. as well as the payroll deductions made to repay the loan

# StaffLoans can be modelled here or in the accounting app depending on how loans are managed in the organization
class LoanType(createdtimestamp_uid):
    name = models.CharField(_("Loan Type"), max_length=100, unique=True) # 
    description = models.TextField(_("Description"), blank=True, null=True)
    interest_rate_type = models.CharField(_("Interest Rate Type"), max_length=20, choices=[
        ('fixed', 'Fixed'),
        ('variable', 'Variable'),
    ], default='fixed')
    interest_rate_scheme = models.CharField(_("Interest Rate Scheme"), max_length=50, choices=[
        ('simple', 'Simple Interest'),
        ('compound', 'Compound Interest'),
    ], default='simple')
    # interest rate calculations can be done monthly, quarterly, annually
    interest_rate_calculation_period = models.CharField(_("Interest Rate Calculation Period"), max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ], default='annually')
    interest_rate = models.DecimalField(_("Interest Rate (%)"), max_digits=5, decimal_places=2, default=0)
    # limits 
    # deduction frequency is by default based on payroll
    # deduction_frequency = models.CharField(_("Deduction Frequency"), max_length=20, choices=[
    #     ('weekly', 'Weekly'),
    #     ('biweekly', 'Biweekly'),
    #     ('monthly', 'Monthly'),
    #     ('quarterly', 'Quarterly'),
    #     ('annually', 'Annually'),
    # ], default='monthly')

    max_loan_amount = MoneyField(_("Maximum Loan Amount"), max_digits=10, decimal_places=2, default_currency='GHS')
    max_repayment_period_months = models.IntegerField(_("Maximum Repayment Period (Months)"), default=0)
    min_monthly_deduction = MoneyField(_("Minimum Monthly Deduction"), max_digits=10, decimal_places=2, default_currency='GHS')
    # percentage of salary that can be deducted monthly for loan repayment
    max_salary_deduction_percentage = models.DecimalField(_("Maximum Salary Deduction Percentage (%)"), max_digits=5, decimal_places=2, default=0)
    # percentage of salary that can be loaned to employee
    max_loan_percentage_of_salary = models.DecimalField(_("Maximum Loan Percentage of Salary (%)"), max_digits=5, decimal_places=2, default=0)
    class Meta:
        verbose_name = _("Loan Type")
        verbose_name_plural = _("Loan Types")

    def __str__(self):
        return self.name


# Deductions and benefits
# Changes to personal or tax information


class StaffLoans(createdtimestamp_uid):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name='staff_loans')
    reason = models.TextField(_("Reason"), blank=True, null=True)
    approval_status = models.CharField(_("Approval Status"), max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending')
    loan_type = models.ForeignKey(LoanType, on_delete=models.PROTECT, related_name='loan_requests')
    loan_amount = MoneyField(_("Loan Amount"), max_digits=10, decimal_places=2, default_currency='GHS')
    # proposed_monthly_deduction = MoneyField(_("Proposed Monthly Deduction"), max_digits=10, decimal_places=2, default_currency='GHS')
    is_disbursed = models.BooleanField(_("Is Disbursed?"), default=False) # indicates whether the loan amount has been disbursed to the employee or not
    est_repayment_period_months = models.IntegerField(_("Estimated Repayment Period (Months)"), default=0)
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    outstanding_balance = MoneyField(_("Outstanding Balance"), max_digits=10, decimal_places=2,  default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies],)
    deduction = MoneyField(_("Salary Transaction Deduction"), max_digits=10, default=0, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies],)
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        # ('defaulted', 'Defaulted'),
    ], default='pending')
    # calc the estimated profit on the interest 
    #    
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name='staff_loans_created')

    class Meta:
        verbose_name = _("Staff Loan")
        verbose_name_plural = _("Staff Loans")

    def __str__(self):
        return f"{self.employee.staff.user.get_full_name()} - {self.loan_amount} ({self.status})"


# payroll model to manage employee salaries, deductions, bonuses, etc.
# the payroll model creates a request for payment for a given period

# class Payroll(createdtimestamp_uid, activearchlockedMixin):
#     # the payroll model will be linked the transaction model in the accounting app to record the payment made to the employee
#     # with a pending status until the payment is processed and when confirmed the transaction model will also generate payslips for employees and deduct taxes and other statutory deductions and account for them in the accounting app
#     # the payroll model will also track any bonuses or deductions applied to the employee's salary
#     # the payroll model will also generate reports for payroll summaries, tax filings, and other statutory requirements and all statutory deductions will be linked to the accounting app for proper tracking and reporting
#     period_start = models.DateField(_("Period Start"))
#     period_end = models.DateField(_("Period End"))
#     total_gross_salary = MoneyField(_("Total Gross Salary"), max_digits=10, decimal_places=2, default_currency='GHS')
#     total_taxed_income = MoneyField(_("Total Taxed Income"), max_digits=10, decimal_places=2, default_currency='GHS')


class Payroll(createdtimestamp_uid):
    
    # change payroll period to month and year date only instead of the range
    date= models.DateField(_("Payroll Date"), auto_now_add=True) #date combines the month and year of the payroll period and is used to determine the payroll period for each employee based on their salary rate period and to facilitate accurate calculation of total gross salary, total taxed income, total deductions, and total net salary for each employee and to ensure proper tracking and reporting of payroll data for financial planning and analysis for both employees and the organization.,
    # the date is always set to the first day of the month to represent the payroll period for that month and year and to facilitate accurate calculation of total gross salary, total taxed income, total deductions, and total net salary for each employee based on their salary rate period and to ensure proper tracking and reporting of payroll data for financial planning and analysis for both employees and the organization.
    # period_start = models.DateField(_("Period Start"))
    # period_end = models.DateField(_("Period End"))
    # employee_count
    # appproved_count
    total_benefits = MoneyField(_("Total Benefits"),default=0, max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies])
    total_gross_salary = MoneyField(_("Total Gross Salary"),default=0, max_digits=10, decimal_places=2,default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies])
    total_taxed_income = MoneyField(_("Total Taxed Income"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies])
    total_deductions = MoneyField(_("Total Deductions"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies])
    total_net_salary = MoneyField(_("Total Net Salary"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies])
    total_loan_deductions = MoneyField(_("Total Loan Deductions"), max_digits=10, decimal_places=2, default_currency=default_currency, currency_choices=[(cur, cur) for cur in allowed_currencies], default=0)
    staff= models.ForeignKey(Staff, on_delete=models.PROTECT, related_name='created_payrolls')
    status = models.CharField(_("Status"), max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
        ('canceled', 'Canceled'),
    ], default='pending')
    class Meta:
        verbose_name = _("Payroll")
        verbose_name_plural = _("Payrolls")
        permissions = [
            ("can_process_payroll", "Can process payroll"),
            ("can_approve_payroll", "Can approve payroll"),
            ("can_reject_payroll", "Can reject payroll"),
            ("can_cancel_payroll", "Can cancel payroll"),
            ('can_view_unpaid_employee_list', 'Can view unpaid employee list'),
            ('can_view_paid_employee_list', 'Can view paid employee list'),
        ]
    
    def save(self, *args, **kwargs):
        # automatically set the payroll date to the first day of the month to represent the payroll period for that month and year and to facilitate accurate calculation of total gross salary, total taxed income, total deductions, and total net salary for each employee based on their salary rate period and to ensure proper tracking and reporting of payroll data for financial planning and analysis for both employees and the organization.
        from datetime import date
        if self.date:
            self.date = self.date.replace(day=1) 
        else:
            raise ValidationError(_("Payroll date must be provided."))
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Payroll for {self.date.strftime('%B %Y')}"
    


class Payrolldetails(createdtimestamp_uid):
    
    status = models.CharField(_("Status"), max_length=50, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ], default='pending')
    # Attendance details
    total_days_worked = models.IntegerField(_("Total Days Worked"), default=0)
    total_hours_worked = models.DecimalField(_("Total Hours Worked"), max_digits=5,
        decimal_places=2, default=0)
    total_overtime_hours = models.DecimalField(_("Total Overtime Hours"), max_digits=5, decimal_places=2, default=0)
    total_leave_days = models.IntegerField(_("Total Leave Days"), default=0)
    total_absent_days = models.IntegerField(_("Total Absent Days"), default=0)
    total_late_days = models.IntegerField(_("Total Late Days"), default=0)
    total_weekend_days = models.IntegerField(_("Total Weekend Days"), default=0)
    total_worked_holiday_days = models.IntegerField(_("Total Worked Holiday Days"), default=0)

    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='payroll_details')
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name='payrolls')
    # benefi
    gross_salary = MoneyField(_("Gross Salary"), max_digits=10, decimal_places=2, default_currency='GHS') #Gross Salary -1000 GHS
    
    taxed_income = MoneyField(_("Taxed Income"), max_digits=10, decimal_places=2, default_currency='GHS') #Tax(10%)= 100 GHS
    deduction = MoneyField(_("Deductions"), max_digits=10, decimal_places=2, default_currency='GHS', null=True, blank=True) #Total Deductions = 50 GHS (medical insurance)
    staffloans=models.ManyToManyField(StaffLoans, verbose_name=_("Staff Loans"), blank=True) # any loan repayments deducted from the employee's salary for that payroll period
    loandeduction = MoneyField(_("Loan Deductions"), max_digits=10, decimal_places=2, default_currency='GHS', null=True, blank=True) # total loan deductions for that payroll period
    net_salary = MoneyField(_("Net Salary"), max_digits=10, decimal_places=2, default_currency='GHS') #Net Salary = 850 GHS
    approved_rejected_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payrolls')

    class Meta:
        verbose_name = _("Payroll_detail")
        verbose_name_plural = _("Payroll_details")
        unique_together = ('employee', 'payroll')
        # permissions = [

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.payroll.date.strftime('%B %Y')}"
    def get_absolute_url(self):
        return reverse("Payroll_detail", kwargs={"pk": self.pk})




class PerformanceEvaluation(createdtimestamp_uid):
    employee = models.ForeignKey(EmployeeManagement, on_delete=models.CASCADE, related_name='performance_evaluations')
    evaluator = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name='evaluations_given')
    skills_assessed = models.ManyToManyField(Skill, verbose_name=_("Skills Assessed"), blank=True)

    date = models.DateField(_("Date"), auto_now_add=True)
    score = models.PositiveIntegerField(_("Score"))
    feedback = models.TextField(_("Feedback"), blank=True, null=True)

    class Meta:
        verbose_name = _("Performance Evaluation")
        verbose_name_plural = _("Performance Evaluations")

    def __str__(self):
        return f"Evaluation for {self.employee.user.get_full_name()} on {self.date}"


    def get_absolute_url(self):
        return reverse("PerformanceEvaluation_detail", kwargs={"pk": self.pk})

```


```python

from typing import Iterable
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from djmoney.money import Money
from accounts.models import calculate_tax_amount
from django.dispatch import receiver
from django.urls import reverse
from addons.models import createdtimestamp, createdtimestamp_uid,discount, activearchlockedMixin
from django.db.models.signals import post_save
from django.utils import timezone
import datetime
from department.models import Department,Branch,Room,Shelfing
from accounts.models import Tax,Transaction,TransactionDoc,Account
from decimal import Decimal
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import ArrayField

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

# from contact.models import Photos
from party.models import Staff

from djmoney.models.fields import MoneyField
from django.db import models


class unit(createdtimestamp_uid,models.Model):
    name = models.CharField(
        _("Unit"),
        unique=True,
        max_length=50,
        help_text=("Examples include tablet,capsule,bottle, strips"),
    )
    is_base_unit=models.BooleanField(_("Is Base Unit"))
    abr = models.CharField(_("Abbreviated as"), max_length=10, blank=True, null=True)

    class Meta:
        verbose_name = _("unit")
        verbose_name_plural = _("units")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("unit_detail", kwargs={"pk": self.pk})

# change this to a unit of measure instead of packsize...
#  and uom conversion ratio instead of packsizes
# sales will be done by a unit of measure

class unitofmeasure(createdtimestamp_uid,models.Model):
    converts_to = models.ForeignKey(
        unit,
        verbose_name=_("Converts To(baseunit)"),
        on_delete=models.CASCADE,
        related_name="to_unit",
        limit_choices_to={"is_base_unit": True},
    )
    converts_from = models.ForeignKey(
        unit,
        verbose_name=_("Converts From"),
        on_delete=models.CASCADE,
        related_name="from_unit",
    )
    conversion_rate = models.PositiveIntegerField(_("Multiplier"), default=1)

    class Meta:
        verbose_name = _("unitofmeasure")
        verbose_name_plural = _("unitofmeasures")
        unique_together=('converts_to','converts_from','conversion_rate')


    def get_absolute_url(self):
        return reverse("unitofmeasure_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if self.converts_to.id == self.converts_from.id:
            self.conversion_rate = 1
        super(unitofmeasure, self).save(*args, **kwargs)  # Call the real save() method

    def __str__(self):
        if self.conversion_rate > 1:
            return f"{self.conversion_rate} {self.converts_to.name} in {self.converts_from.name}" 
        else:
            return f"{self.converts_from.name}"



@receiver(post_save, sender=unit)
def load_form_data(sender, instance=None, created=False, **kwargs):
    if created:
        if instance.is_base_unit:
            unitofmeasure.objects.get_or_create(converts_to=instance, converts_from=instance, conversion_rate=1)


class Manufacturer(createdtimestamp_uid, models.Model):
    # to be made obsolete as manufacturers are to be moved to party app as part of vendors


    brand_grade_categ = (
        ("Premium", "Premium"),
        ("Superior", "Superior"),
        ("Regular", "Regular"),
        ("ValuePackage", "ValuePackage"),
        ("LowEnd", "LowEnd"),
    )

    brand_category = models.CharField(
        _("Brand Grading Category"), max_length=14, choices=brand_grade_categ,default='Regular'
    )

    name = models.CharField(_("Manufacturer"), max_length=50, unique=True)
    description = models.CharField(_("Description"), max_length=200, null=True, blank=True)

    class Meta:
        verbose_name = _("Manufacturer")
        verbose_name_plural = _("Manufacturers")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("manufacturer_detail", kwargs={"pk": self.pk})

class VariantType(createdtimestamp_uid):
    '''
    Product variation types generally depend on the nature of the products and their customizable attributes. Here’s a comprehensive list of commonly used product variation types:

    ### Physical Attributes
    1. **Color**: Variations in color (e.g., Red, Blue, Green).
    2. **Size**: 
    - Numerical sizes (e.g., 39-42 for shoes).
    - Alphabetical sizes (e.g., S, M, L, XL).
    3. **Material**: Type of material (e.g., Cotton, Leather, Plastic).
    4. **Shape**: Variations in shape (e.g., Round, Square).
    5. **Pattern**: Patterns or designs (e.g., Striped, Solid, Polka Dots).
    6. **Weight**: Different weight options (e.g., 500g, 1kg).
    7. **Dimensions**: Variations in length, width, or height (e.g., 10cm x 15cm, 20cm x 30cm).

    ### Functional Attributes
    8. **Capacity**: Variations in storage or performance capacity (e.g., 16GB, 32GB for storage devices).
    9. **Power**: Power-related differences (e.g., 500W, 1000W for appliances).
    10. **Speed**: Different speed levels (e.g., 2.0 GHz, 3.0 GHz for processors).
    11. **Compatibility**: Compatibility with different systems or devices (e.g., iOS, Android).

    ### Packaging Variations
    12. **Bundle Options**: Variations in package size (e.g., Single, Pack of 3).
    13. **Quantity**: Number of items in a pack (e.g., 6-pack, 12-pack).
    14. **Packaging Type**: Variations in packaging (e.g., Box, Bag, Bottle).

    ### Personalization Options
    15. **Engraving**: Custom text or designs on the product.
    16. **Custom Prints**: Personalized images or patterns.
    17. **Monograms**: Initials or logos added to the product.

    ### Seasonal or Thematic Variations
    18. **Seasonal Themes**: Products designed for specific seasons (e.g., Winter, Summer collections).
    19. **Limited Editions**: Special, time-limited variations.

    ### Digital or Software Variations
    20. **Version**: Different versions of software (e.g., Standard, Pro).
    21. **License Type**: Single-user or multi-user license options.

    ### Regional or Cultural Variations
    22. **Language**: Variations based on language (e.g., English, Spanish).
    23. **Cultural Customizations**: Specific designs or features tailored for cultural preferences.

    ### Miscellaneous
    24. **Flavor**: Variations in flavor (e.g., Chocolate, Vanilla).
    25. **Fragrance**: Variations in scent (e.g., Lavender, Citrus).
    26. **Style**: Variations in design style (e.g., Classic, Modern).
    27. **Finish**: Surface finish variations (e.g., Glossy, Matte).
    28. **Voltage**: Variations in electrical voltage requirements (e.g., 110V, 220V).

    Let me know if you’d like further clarification on any of these or need help integrating them into a system!

    '''

    name = models.CharField(max_length=50, unique=True,null=False,blank=False)# eg:Size(Alpha) or Size(Number)  and/or Color,
    description=models.CharField(_("Description"), max_length=225,null=True,blank=True)
    multiselect=models.BooleanField(_("Multiple Selection Allowed"),default=False, help_text=_("If true, product can have multiple attributes of this variant type. e.g. A shirt can be both Red and Blue"))
    class Meta:
        verbose_name = _("VariantType")
        verbose_name_plural = _("VariantTypes")
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # capitalize the first letter of the name
        #
        self.name = self.name.capitalize()
        super(VariantType, self).save(*args, **kwargs)




class Category(createdtimestamp_uid, models.Model):

    name = models.CharField(_("Category Name"), max_length=50, unique=True)
    description = models.CharField(
        _("Description"), max_length=250, null=True, blank=True
    )
    # Here say category of shoes can have as many variant type as they want and hence creating variants attributes of the product


    class Meta:
        verbose_name = _("Products Category")
        verbose_name_plural = _("Products Categories")

    def save(self, *args, **kwargs):
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("category_detail", kwargs={"pk": self.pk})


class isserviceitemmanager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_serviceitem=True)



class selling_rules(createdtimestamp_uid):
    '''
    # Write description

    Selling Rule Department 
    '''
    department = models.ForeignKey(
        Department, verbose_name=_("Department"), on_delete=models.CASCADE
    )
    # default=models.BooleanField(_("Default selling rules"))
    name=models.CharField(_("Selling Rule"), max_length=50)
    description=models.TextField(_("Description"),null=True,blank=True)
    # Permissions and 
    variant_prices_allowed=models.BooleanField(_("Variant Prices Allowed"),default=False)
    discount_allowed = models.BooleanField(_("Sale Discount Allowed"), default=False)
    service_item_included = models.BooleanField(_("Service Item Included"), default=False)
    coupon_restricted = models.BooleanField(_("Coupon Restricted"), default=False)
    price_entry_required = models.BooleanField(_("Price Entry Required"), default=False)
    weight_entry_required = models.BooleanField(_("Weight Entry Required"), default=False)
    employee_discount_allowed = models.BooleanField(_("Employee Discount Allowed"), default=False)
    allow_food_stamp = models.BooleanField(_("Allow Food Stamp"), default=False)
    
    tax_exempt = models.BooleanField(_("Tax Exempt"), default=False)
    tax_excluded_in_prices=models.BooleanField(_("Tax Excluded in Prices"), default=False) 
    # default false means for the product taxes are always going to be included in the selling price
    # so for example if 200 as selling price and 10% tax then tax amount is 180 and the amount saved or recieved is 200
    # if false total amount should be 220


    prohibit_repeat_key = models.BooleanField(_("Prohibit Repeat Key Usage"), default=False)
    frequent_shopper_eligibility = models.BooleanField(_("Frequent Shopper Points Eligibility"), default=False)
    frequent_shopper_points = models.PositiveIntegerField(
        _("Frequent Shopper Points Count"), default=0,
        help_text=_("Points awarded for frequent shopper programs")
    )
    # Additional settings
    age_restrictions = models.BooleanField(_("Age Restriction"), default=False)
    return_allowed = models.BooleanField(_("Return Allowed"), default=False)
    as_product_discount = models.BooleanField(_("Apply as Product Discount"), default=False)

    credit_sales_allowed=models.BooleanField(_("Can Be Sold On Credit?"),default=False)
    # online prices
    # allow switch to wholesale prices
    # special discount per quantity

    # consider for onlineproducts and pricing
    # MinimumSaleUnitCount 
    # MaximumSaleUnitCount
    
    def clean_taxables(self):
        if self.tax_exempt:
            self.tax_excluded_in_prices = False
        pass
    
    def clean(self):
        self.clean_taxables()
        return super().clean()
    
    def save(self, *args, **kwargs):
        super(selling_rules, self).save(*args, **kwargs) # Call the real save() method


    class Meta:
        verbose_name = _("Selling Rule")
        verbose_name_plural = _("Selling Rules")
        ordering = ['department', 'name']
        unique_together=('name','department')

    def __str__(self):
        return f"{self.name}-{self.department.name}"

    def get_absolute_url(self):
        return reverse("selling_rule_detail", kwargs={"pk": self.pk})
    
    class Meta:
        verbose_name = _("selling_rules")
        verbose_name_plural = _("sellings_rules")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("selling_detail_rules", kwargs={"pk": self.pk})



class VariantAttribute(createdtimestamp_uid):
    variant_type = models.ForeignKey(VariantType, on_delete=models.CASCADE, related_name='product_attributes')
    name = models.CharField(max_length=50)# ok so in for Size(Alpha),() or Size(Number)  and/or Color,
    description=models.CharField(_("Description"), max_length=225,null=True, blank=True)
    
    def __str__(self):
        return f"{self.variant_type.name}: {self.name}"
    
    class Meta:
        verbose_name = _("Variant Attribute")
        verbose_name_plural = _("variant Attributes")
        unique_together=('variant_type','name')

# https://www.omg.org/retail-depository/arts-odm-73/logical_01010.htm


# class merchandize(createdtimestamp_uid):
#     '''
#     this name is given by a supplier of an item and is different from the name the retailer refers the item.
#     can be the same.
#     This is to allow the mapping of products on the supplier invoice to the direct typed invoice.
#     hence once the picture is uploaded, autofill the items and fill the invoice
#  
#     '''

#     name=models.CharField(_("Name"), max_length=50)
#     description=models.CharField(_("Description"), max_length=50)

#     class Meta:
#         verbose_name = _("merchandize")
#         verbose_name_plural = _("merchandizes")

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse("merchandize_detail", kwargs={"pk": self.pk})


class Item( createdtimestamp_uid, models.Model):
    
    choicestatus=(
        ('archived','archived'),
        ('locked','locked'),
        ('deleted','deleted'),
        ('active','active')
    )
    status=models.CharField(_("Status"),choices=choicestatus,default='active', max_length=50)
    category = models.ForeignKey(
        Category,
        verbose_name=_("Products category"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="item_category",
    )
    pictures = ArrayField(models.CharField(max_length=200, null=False, blank=False), blank=True, default=list)
    barcodes = ArrayField(models.CharField(max_length=100, null=False, blank=False), blank=True, default=list)
    name = models.CharField(
        _("Item Name"),
        max_length=255,
        null=False,blank=False
    )
    namestrip=models.CharField(_("Name Strip"), max_length=255,null=False,blank=False,editable=False, unique=True,)
    brandname= models.CharField(
        _("Brand Name"),
        max_length=255,null=True,blank=True
    )
    description = models.TextField(_("Description"), blank=True, null=True)
    manufacturer = models.ForeignKey(
        Manufacturer,
        verbose_name=_("Manufacturer Brand"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    has_variants=models.BooleanField(
        _("Has Variants"),
        default=False
        ) # by default if a product has variants then the variants can have varried prices or costs, however defaults to the already set price or cost price
    item_variants_types = models.ManyToManyField(
        VariantType,
        verbose_name=_("Item Variant Types"),
        blank=True,
    )
    is_manufactured=models.BooleanField(
        _("Is Manufactured"),
        default=False
    )
    is_raw_material=models.BooleanField(
        _("Is Raw Material"),
        default=False
    )
    # for internal use only means the product can be bought but not sold and is primarily for internal consumption
    # such as cleaning supplies,stationery etc
    # such products are primarily to be used in departments and not sold to customers and the inventory states are primarily monitored for internal use and by the HRM module
    is_internaluseonly=models.BooleanField(
        _("Is Internal Use Only"),
        default=False
    )
    
    # products with is_internaluseonly cannot be sold in sales transactions 
    # products with is_internaluseonly false can be transfered out of a branches inventory to another branch or hrm inventory for internal use
    # manufactured products that have a boolean feild showing that a Bill of Materials 
    # raw products have a boolean feild showing that they are purchased items 
    # variants with different prices will be handled in the item pricing per department model
    variants_price_allowed=models.BooleanField(_("Variants Price Allowed"), default=False)
    is_expiry_tracked=models.BooleanField(_("Is Expiry Tracked"),default=False,help_text=_("Check if the product has an expiry date"))
    unit = models.ForeignKey(
        unit,
        verbose_name=_("Unit"),
        on_delete=models.CASCADE,
    )  # this will inform the kind of information saved in the packsize details
    
    substitutebrands = models.ManyToManyField(
        "self",
        verbose_name=_("Product Substitutes"),
        blank=True,
    )
    
    is_serviceitem = models.BooleanField(
        _("Is Service Item"), default=False
    )  ##service items include bp checks, sugar tests and other service charged processes that bring in sales and not necessarily involve inventory change.

    # if service item is unselected the product needs to be updated with quantities currently in stock
    # retails sold as dossage form that is base, wholesales sold as
    objects = models.Manager()
    service_items = isserviceitemmanager()
    
    service_added =models.ManyToManyField("self",verbose_name=_("Service item sold with"),
        blank=True
        )


    def clean_barcodes(self):
        # ensure that barcodes are unique across products
        # check for dupplicate product barcodes
        # get all barcodes from other products
        if self.is_serviceitem:
            if len(self.barcodes) > 0:
                raise ValidationError(
                    {"barcodes": _("Service items cannot have barcodes.")}
                )

        barcode_set = set(Item.objects.exclude(pk=self.pk).values_list('barcodes', flat=True))

        for barcode in self.barcodes:
            if barcode in barcode_set:
                raise ValidationError(
                    {"barcodes": _("Duplicate barcodes are not allowed within the same product.")}
                )

        pass    
    

    def clean_varianttypes(self):
        # for now pass
        # if self.category.variantType is None and self.has_variants:
        #     raise ValidationError(
        #         {"varianttypes": _("If product has variants, please select the various variant types.")}
        #     )
        # else:
        #     pass
        # if self.has_variants:
        #     if self.item_variants_types.count() == 0:
        #         raise ValidationError(
        #             {"varianttypes": _("If product has variants, please select the various variant types.")}
        #         )
        if self.variants_price_allowed and not self.has_variants:
            raise ValidationError(
                {"variants_price_allowed": _("Variants Price Allowed can only be true if product has variants.")}
            )
        
        if self.is_serviceitem and self.has_variants:
            raise ValidationError(
                {"has_variants": _("Service Items Can Not have variants"),
                 "is_serviceitem": _("Service Items Can Not have variants")
                }
            )
        else:
            pass

        pass

    def clean(self):
        self.clean_varianttypes()
        self.clean_barcodes()
        return super().clean()


    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")
        indexes = [
            models.Index(fields=['name', 'namestrip', 'brandname']),  # Multi-field index
        ]

    def save(self, *args, **kwargs):
        if self.substitutebrands is not None:
            self.substituteidentified = True
        self.namestrip = slugify(self.name.lower().strip())
        super(Item, self).save(*args, **kwargs)  # Call the real save() method

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        return reverse("Item_detail", kwargs={"pk": self.pk})






class item_pricing_department(createdtimestamp_uid,discount):
    sale_department = models.ForeignKey(
        Department,
        verbose_name=_("Department"),
        on_delete=models.CASCADE,
        related_name="saledepartment",
    )
    selling_rules=models.ForeignKey(selling_rules, verbose_name=_("Selling Rules"), on_delete=models.SET_NULL,null=True, blank=True)
    item = models.ForeignKey(
        Item,
        verbose_name=_("Item"),
        on_delete=models.CASCADE,
        related_name="productpricing",
    )
    selling_price = MoneyField(
        _("Selling Price"),
        max_digits=20,
        decimal_places=2,
        default=0,default_currency='GHS'
    )
    employee_discount = models.DecimalField(    
        _("Employee Discount"), max_digits=20, decimal_places=2, default=0
    )
    uom= models.ForeignKey(
        unitofmeasure,
        verbose_name=_("Selling Pack Size"),
        on_delete=models.CASCADE,
    )                           
    def save(self, *args, **kwargs):
        
        super().save(*args, **kwargs)

    def clean_prevent_serviceitem_variant(self):
        # service items cannot be created(or serve as inventory items.)
        # if self.item.is_serviceitem:
        #     raise ValidationError(
        #             {"is_serviceitem": _("Service Items Can Not have variants")}
        #    )
        pass

    def is_discount_allowed(self):
        return self.selling_rules.discount_allowed

    def clean_services(self):
        if self.item.is_serviceitem and not self.uom.conversion_rate == 1:
            raise ValidationError(
                {"selling_rules": _("The selected selling rules do not allow service items.")}
            )
        else:
            pass

    def clean(self):
        self.clean_discount()
        self.clean_employee()
        self.clean_services()
        return super().clean()
    
    def clean_employee(self):
        """
        Clean Employee Discount
        Model-level validation.
        Ensures that 'discount' is valid based on 'discount_type'.
        """
        if self.discount_type == "percent" and not (0 <= self.employee_discount <= 1):
            raise ValidationError(
                {"discount": _("For percent discounts, the employee value must be between 0 and 1.")}
            )
        
        elif self.discount_type == "amount" and self.employee_discount < 0:
            raise ValidationError(
                {"discount": _("For amount discounts, the employee value must be non-negative.")}
            )
        else:
            pass

    @property
    def discounted(self):
        # if self.selling_rules.filter(discount_allowed=True).exists():
        if self.selling_rules is not None and self.selling_rules.discount_allowed:
            # print(self.discount_type == 'percent')
            """Calculate discount based on the selected discount type."""
            if self.discount_type == 'percent':
                discounted= self.selling_price*self.discount
                return discounted
            elif self.discount_type == 'amount':
                discounted= Money(self.discount,self.selling_price.currency)
                return discounted
        else:
            return Money(0,self.selling_price.currency)
            
    @property
    def empdiscounted(self):
        # if self.selling_rules.filter(discount_allowed=True).exists():
        if self.selling_rules is not None and self.selling_rules.employee_discount_allowed:
            """Calculate discount based on the selected discount type."""
            if self.discount_type == 'percent':
                discount=self.selling_price * self.employee_discount
                return discount
            elif self.discount_type == 'amount':
                return Money(self.employee_discount,self.selling_price.currency)
        else:
            return Money(0,self.selling_price.currency)

    # @property
    # def final_taxamount_emp(self):
    #     if self.selling_rules and not self.selling_rules.tax_exempt:
    #         taxamount=sum([calculate_tax_amount(self.empdiscounted, tax.id)[0] for tax in self.tax.all()])
    #         return taxamount+self.empdiscounted
    #     return self.empdiscounted
    

    
    class Meta:
        verbose_name = _("item_pricing")
        verbose_name_plural = _("item_pricings")
        unique_together = ("sale_department", "item", "uom")
        indexes = [
            models.Index(fields=["sale_department", "item", "uom"]),  # Multi-field index
        ]

    def __str__(self):
        return f"Pricing for {self.item.name} in {self.sale_department.name}"

    def get_absolute_url(self):
        return reverse("item_pricing_detail", kwargs={"pk": self.pk})





class ItemLot(createdtimestamp_uid):
    status=models.CharField(_("Status"),max_length=20 , choices=(('active','active'),('inactive','inactive')),default='active')
    item = models.ForeignKey(Item, verbose_name=_("Product"), on_delete=models.PROTECT,related_name='itemlot',
                             limit_choices_to={
                                 'is_serviceitem':False
                             })
    lot_number = models.CharField(_("Batch or Lot Number"), max_length=255) #auto generate lot_number
    manufacturing_date = models.DateField(_("Manufacturing Date"),blank=True,null=True,)
    expiry_date = models.DateField(
        _("Expiry Date"),
        blank=True,
        null=True,
    )
    uom = models.ForeignKey(
        unitofmeasure, verbose_name=_("Pack Details"), on_delete=models.PROTECT
    )
    
    # write a clean function to ensure that the expiry date is not before the manufacturing date
    def clean_manufacturing_date(self):
        if self.manufacturing_date > self.expiry_date:
            raise ValidationError(
                {"manufacturing_date": _("Manufacturing date cannot be after expiry date.")}
            )
        elif self.manufacturing_date > self.expiry_date:
            raise ValidationError(
                {"expiry_date": _("Expiry date cannot be before manufacturing date.")}
            )
        else:
            pass
    

    # write a clean function to ensure that if product can expire, manufacturing date and expiry date are not null
    def clean_expiry_date(self):
        if self.item.is_expiry_tracked:
            if self.manufacturing_date is None:
                raise ValidationError(
                    {"manufacturing_date": _("Product can expire. Manufacturing date cannot be null.")}
                )
            if self.expiry_date is None:
                raise ValidationError(
                    {"expiry_date": _("Product can expire. Expiry date cannot be null.")}
                )
            
            pass
        pass
    
    def clean(self):
        self.clean_expiry_date()
        self.clean_manufacturing_date()
        return super().clean()
    @property
    def can_expire(self):
        return self.item.is_expiry_tracked
    
    @property
    def is_expired(self):
        if self.can_expire:
            return self.expiry_date <= datetime.date.today()
        return False

    @property
    def days_to_expiry(self):
        if self.is_expired:
            return 0
        elif self.can_expire:
            return (self.expiry_date - datetime.date.today()).days
        return None

    @property
    def months_to_expiry(self):
        if self.is_expired:
            return 0
        today = datetime.date.today()
        months = (self.expiry_date.year - today.year) * 12 + (
            self.expiry_date.month - today.month
        )
        if self.expiry_date.day < today.day:
            months -= 1
        return months

    # def close_to_expiry_discounted(self):
    #     if self.item.is_discount_allowed() and not self.is_expired:
    #         if self.months_to_expiry <= 1:
    #             return 0.2
    #         elif self.months_to_expiry <= 2:
    #             return 0.1
    #         elif self.months_to_expiry <= 3:
    #             return 0.05
    #     return None

    class Meta:
        verbose_name = _("ItemLot")
        verbose_name_plural = _("ItemLots")
        unique_together = ("item", "lot_number", )

    def __str__(self):
        if self.item.is_expiry_tracked:
            return f'{self.item.name}--{self.lot_number}(Expiry: {self.expiry_date})'
        return f'{self.item.name}'

    def save(self, *args, **kwargs):
        # if self.item.is_expiry_tracked:


        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("itemlot_detail", kwargs={"pk": self.pk})


class StockLotCostValuation(createdtimestamp_uid):

    '''
    cost method used

    (Quantity on hand * current cost) + (Quantity received * Receipt cost)
    ____________________________________________________________________
    (Quantity on hand) + (QuantityRecieved)


    Transfer between Departments should also elicit the creation and or update of this table using the same formula

    '''
    itemlot = models.ForeignKey(
        ItemLot, verbose_name=_("Lot"), on_delete=models.CASCADE, related_name='costvaluation'
    )
    cost_department = models.ForeignKey(
        Department,
        verbose_name=_("Department"),
        on_delete=models.CASCADE,
    )
    uom=models.ForeignKey(unitofmeasure, verbose_name=_("UOM"), on_delete=models.CASCADE,limit_choices_to={'conversion_rate':1})
    # make default currency value be that of the company base currency
    cost_price = MoneyField(
        _("Unit Cost Price(Default Currency)"),
        max_digits=20,
        decimal_places=2,
        default=0,
        default_currency='GHS'
    )
    # cost price in stock valuation must always be in the base currency of the company and never changed
    

    def clean_uom(self):
        if self.uom.conversion_rate != 1:
            raise ValidationError(
                {"uom": _("UOM must be base unit to calculate cost.")}
            )
        if self.uom.converts_to is not self.itemlot.item.unit:
            raise ValidationError(
                {"uom": _("The Stock Lot Cost Valuation UOM must be the same base unit on the Item.")}
            )
        pass

    def clean(self):
        self.clean_uom()
        return super().clean()
    class Meta:
        verbose_name = _("StockLotCostValuation")
        verbose_name_plural = _("StockLotCostValuations")
        unique_together=('itemlot','cost_department')

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to set the initial beginning count on create."""
        self.clean()
        super(StockLotCostValuation, self).save(*args, **kwargs)


    def get_absolute_url(self):
        return reverse("StockLotCostValuation_detail", kwargs={"pk": self.pk})


# ok move the creation of product variants to the creation of product inventory



class ItemInventoryLot(createdtimestamp_uid, models.Model):
    item = models.ForeignKey(Item, verbose_name=_("Product"), on_delete=models.CASCADE)
    itemlot = models.ForeignKey(
        ItemLot, verbose_name=_("ItemLot"), on_delete=models.CASCADE
    )
    location = models.ForeignKey(
        Branch, verbose_name=_("Branch Location"), on_delete=models.CASCADE
    )
    qty = models.PositiveIntegerField(_("Qty"),default=0)
    # base_qty = models.PositiveIntegerField(_("Base Qty"))
    shelfnumber = models.ForeignKey(
        Shelfing,
        verbose_name=_("Shelf Number"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    inventory_state_choices = (
        ("OnHand", "On Hand"),#these are returnable,saleable and transferable
        ("OnOrder", "On Order"),#reserved inventory for paid products
        ("OnLayaway", "On Layaway"),#for installment and or partpaid product
        ("Damaged", "Damaged"),#these are returnable
        ("OnHold", "On Hold"),# holding state for transactions,return state etc
    )
    inventory_state = models.CharField(
        _("Inventory State"),
        max_length=50,
        choices=inventory_state_choices,
        default="OnHand",
    )
    
    @property
    def packsizing(self):
        return self.itemlot.uom.conversion_rate

    @property
    def packname(self):
        return self.itemlot.uom.converts_from

    @property
    def is_itemlot_expired(self):
        return self.itemlot.is_expired

    class Meta:
        verbose_name = _("ItemInventoryLot")
        verbose_name_plural = _("ItemInventoryLots")
        unique_together = ("itemlot", "location", "inventory_state")

    def save(self, *args, **kwargs):
        """Override save to set the initial beginning count on create."""
        self.item = self.itemlot.item
        super(ItemInventoryLot, self).save(*args, **kwargs)

    def __str__(self):
        return self.itemlot.item.name

    def get_absolute_url(self):
        return reverse("ItemInventoryLot_detail", kwargs={"pk": self.pk})


class itemvariant(createdtimestamp_uid):
    name=models.CharField(_("Name"), max_length=50)
    item=models.ForeignKey(Item, verbose_name=_("Item"), 
            on_delete=models.CASCADE,
            limit_choices_to={"has_variants": True},
            related_name='variants'
            )
    variant=models.ManyToManyField(VariantAttribute, verbose_name=_("Variant Attribute Types"))
    pictures = ArrayField(models.CharField(max_length=200), blank=True, default=list)

    # ensure that the variant pictures belong to the same item

    def clean_pictures(self):
        
        pass

    def clean(self):
        self.clean_pictures()
        return super().clean()
    class Meta:
        verbose_name = _("item variant")
        verbose_name_plural = _("item variants")
        unique_together=('name','item')



    def checkvarianttype(self):
        # check if item has_variants is true and make sure that the variantattributes selected correspond to the product varianttype on the categort table

        # Check if variants selected belongs to the same product category variant type
        # if self.category.variantType is not None:

        pass


    def clean(self):
        self.checkvarianttype()
        
        return super().clean()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("itemvariant_detail", kwargs={"pk": self.pk})

class itemvariantprices(createdtimestamp_uid):
# separate this feature
    variant_item=models.ForeignKey(itemvariant, verbose_name=_("Item Variants"),  on_delete=models.CASCADE,related_name='variantsproductprice')
    itempricingdepartment=models.ForeignKey(item_pricing_department, verbose_name=_("Item Pricing Department"), on_delete=models.CASCADE,related_name='variantspricingdepartment')
    selling_price = MoneyField(
        _("Variant Selling Price"),
        max_digits=20,
        decimal_places=2,
        default=0,default_currency='GHS'
    )
    class Meta:
        verbose_name = _("itemvariantprices")
        verbose_name_plural = _("itemvariantpricess")
        unique_together=('variant_item','itempricingdepartment')

    def __str__(self):
        return self.variant_item

    def get_absolute_url(self):
        return reverse("itemvariantprices_detail", kwargs={"pk": self.pk})



class ItemInventoryLotVariant(createdtimestamp_uid):

    lot=models.ForeignKey(ItemInventoryLot, verbose_name=_("Inv Lot"), on_delete=models.CASCADE, related_name='variantlotsquant')
    variant=models.ForeignKey(itemvariant, verbose_name=_("Variant"), on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(_("Base Qty"))
    class Meta:
        verbose_name = _("ItemInventoryLotVariant")
        verbose_name_plural = _("ItemInventoryLotVariants")
        unique_together=('lot','variant')

    # def save(self, *args, **kwargs):
    #     # """Override save to set the initial beginning count on create."""
    #     # if self._state.adding:
    #     #         super(ItemInventoryLot, self).save(*args, **kwargs)


    
    def clean_item_id(self):
        """
        Clean item ID 
        Model-level validation.
        Ensures that Item ID for lot and variant types are always the same.
        """
        if self.lot.item.id != self.variant.item.id:
            raise ValidationError(
                {"varianttype": _("Variant Type and Item Lots must be same always.")}
            )
        else:
            pass

    def clean(self):
        self.clean_item_id()
        return super().clean()

    def __str__(self):
        return self.varianttype.variant
    

    def get_absolute_url(self):
        return reverse("ItemInventoryLotVariant_detail", kwargs={"pk": self.pk})

# to be rewritten 
class StockLedgerEntry(createdtimestamp_uid):
    
    
    branch=models.ForeignKey(Branch, verbose_name=_("Branch"), on_delete=models.CASCADE)
    # account=models.ForeignKey(Account, verbose_name=_("Account"), on_delete=models.CASCADE)# the specific inventory account associated with the inventory branch affected
    transaction=models.ForeignKey(Transaction, verbose_name=_("Stock Ledger Entry"), on_delete=models.CASCADE)
    stockvaluation=MoneyField(
        _("Stock Cost Valuation"),
        max_digits=20,
        decimal_places=2,
        default=0,default_currency='GHS'
    )
    transaction_type = models.CharField(
        _("Transaction Type"),
        max_length=10,
        choices=(("Debit", "Debit"), ("Credit", "Credit")),
    )
    # increase === debit
    # decrease== credit
    inventorytransacttype = models.CharField(
        _("Transaction Type"),
        max_length=10,
        choices=(("Increase", "Increase"), ("Decrease", "Decrease")),
    )
    
    ALLOWED_MODELS = ['ReturnDocumentBranch','InventoryTransaction','Bill','TransferInventoryDocument','AdjustmentDocumentBranch']

    #list the models that affect the accounting model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    transaction_object = GenericForeignKey("content_type", "object_id")
    
    def clean_allowed_models(self):
        print(self.content_type.model)
        if self.content_type.model not in self.ALLOWED_MODELS:

            raise ValidationError(f"Invalid Transaction Doc: {self.content_type.model}")
        pass
    def clean(self):
        self.clean_allowed_models()
        return super().clean()

    class Meta:
        verbose_name = _("StockLedgerEntry")
        verbose_name_plural = _("StockLedgerEntrys")
        unique_together = (("branch", "transaction"),)

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("StockLedgerEntry_detail", kwargs={"pk": self.pk})
    # write a function to check if the each stockledger entry stock is the same as the sum of the iteminventoryjournalentry


# class StockLedgerEntrydetail(models.Model):
#     transaction=models.ForeignKey(StockLedgerEntry, verbose_name=_("StockLedgerEntry"), on_delete=models.CASCADE)
#     location = models.ForeignKey(
#         Branch, verbose_name=_("Branch Location"), on_delete=models.CASCADE
#     )
#     stockvaluation=models.DecimalField(
#         _("Stock Valuation"),
#         max_digits=20,
#         decimal_places=2,
#         default=0,
#     )
    
#     class Meta:
#         verbose_name = _("StockLedgerEntrydetail")
#         verbose_name_plural = _("StockLedgerEntrydetails")

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse("StockLedgerEntrydetail_detail", kwargs={"pk": self.pk})


class itemInvJournalEntry(createdtimestamp_uid):
    '''
    This Journal Entry Method should ensure that the inventory states for all inventory states are monitored
    # Inventory details(source branch)
    1. Inventory state
    2. Inventory state before transaction
    # inventory states
    3. Transaction details
    4. Inventory state valuation
    5. Transaction Type
    6. referrence objects for the source of the inventory transaction change
    7. 
    '''

    stockledger=models.ForeignKey(StockLedgerEntry, verbose_name=_("StockLedgerEntry"), on_delete=models.CASCADE,related_name='itemInvJournalEntries')
    itemlot = models.ForeignKey(
        ItemLot, verbose_name=_("ItemLot"), on_delete=models.CASCADE
    )
    location = models.ForeignKey(
        Branch, verbose_name=_("Branch Location"), on_delete=models.CASCADE
    )
    qty = models.PositiveIntegerField(_("Base Quantity"),editable=False,default=0)
    inventory_state_choices = (
        ("OnHand", "On Hand"),#these are returnable,saleable and transferable
        ("OnOrder", "On Order"),#reserved inventory for paid products
        ("OnLayaway", "On Layaway"),#for installment and or partpaid product
        ("Damaged", "Damaged"),#these are returnable
        ("OnHold", "On Hold"),# holding state for transactions,return state etc
    )
    uom=models.ForeignKey(
        unitofmeasure, verbose_name=_("UOM"), on_delete=models.CASCADE
    )
    uom_qty = models.PositiveIntegerField(_("UOM Quantity"))

    inventory_state = models.CharField(
        _("Inventory State"),
        max_length=50,
        choices=inventory_state_choices,
        default="OnHand",
    )
    stock_valuation_unit=MoneyField(
        _("Stock Valuation Unit"),
        max_digits=20,
        decimal_places=2,
        default=0,default_currency='GHS'
    )
    stock_valuation_line=MoneyField(
        _("Stock Valuation Line"),
        max_digits=20,
        decimal_places=2,
        default=0,default_currency='GHS'
    )
    beginning_unit_count_base = models.PositiveIntegerField(
        _("Beginning Base Quantity"), default=0, blank=True, null=True
    )
    gross_sales_unit_count_base = models.PositiveIntegerField(
        _("Gross Sales Base Quantity"), default=0, blank=True, null=True
    )
    return_unit_count_base = models.PositiveIntegerField(
        _("Return Quantity base"), default=0, blank=True, null=True
    )
    received_unit_count_base = models.PositiveIntegerField(
        _("Received Quantity base"), default=0, blank=True, null=True
    )
    received_from_vendor_unit_count_base = models.PositiveIntegerField(
        _("Received From Vendor Quantity base"), default=0, blank=True, null=True
    )
    return_to_vendor_unit_count_base = models.PositiveIntegerField(
        _("Return To Vendor Quantity base"), default=0, blank=True, null=True
    )
    transfer_in_unit_count_base = models.PositiveIntegerField(
        _("Transfer In Base Quantity"), default=0, blank=True, null=True
    )
    transfer_out_unit_count_base = models.PositiveIntegerField(
        _("Transfer Out Base Quantity"), default=0, blank=True, null=True
    )
    increase_adjustment_unit_count_base = models.PositiveIntegerField(
        _("Increase Adj Base Quantity"), default=0, blank=True, null=True
    )
    decrease_adjustment_unit_count_base = models.PositiveIntegerField(
        _("Decrease Adj Base Quantity"), default=0, blank=True, null=True
    )
    # only details are allowed here
    ALLOWED_MODELS = [
        'ReturnDocumentBranch', 'InventoryTransaction', 'BillDetails', 'TransferDocumentBranch', 'AdjustmentDocumentBranch','Sale_Return'
    ]
    #list the models that affect the accounting model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    object = GenericForeignKey("content_type", "object_id")
    
    def clean_allowed_models(self):
        if self.content_type.model not in self.ALLOWED_MODELS:
            raise ValidationError(f"Invalid Transaction Doc: {self.content_type.model}")
        # always enure that all the following fields are not null
        # stock_valuation_unit
        # stock_valuation_line
        # itemlot, location, inventory_state, stockledger,uom, uom_qty
        if not all([self.itemlot, self.location, self.inventory_state, self.stockledger, self.uom, self.uom_qty]):
            raise ValidationError(_("All fields must be provided and not null."))
        pass
    def clean(self):
        self.clean_allowed_models()
        return super().clean()

    class Meta:
        verbose_name = _("itemInvJournalEntry")
        verbose_name_plural = _("itemInvJournalEntries")
        unique_together = ("itemlot", "location", "inventory_state", "stockledger",'uom')
    def __str__(self):
        return self.itemlot.item.name

    def get_absolute_url(self):
        return reverse("itemInvJournalEntry_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        self.clean()
        """Override save to set the initial beginning count on create."""
        self.qty= self.uom.conversion_rate * self.uom_qty
        if self._state.adding:
            # record every instance and change in the transaction document
            # check if itemlot and branch does not exist, then set the BeginningUnitCountbase to the qty
            if not ItemInventoryLot.objects.filter(
                itemlot=self.itemlot, location=self.location, inventory_state=self.inventory_state
            ).exists():
                self.BeginningUnitCountbase = self.qty
            # if 
            pass
        
        super(itemInvJournalEntry, self).save(*args, **kwargs)


@receiver(post_save, sender=itemInvJournalEntry)
def update_itemlotinventory(sender, instance, created, **kwargs):
    if created:
        # Create a new ItemLotInventory instance
        if instance.stockledger.inventorytransacttype == 'Increase':
            # Increase the quantity in the ItemInventoryLot
            item_inventory_lot, created = ItemInventoryLot.objects.get_or_create(
                itemlot=instance.itemlot,
                location=instance.location,
                inventory_state=instance.inventory_state,
            )
            item_inventory_lot.qty += instance.qty
            item_inventory_lot.save()
        elif instance.stockledger.inventorytransacttype == 'Decrease':
            # Decrease the quantity in the ItemInventoryLot
            item_inventory_lot, created = ItemInventoryLot.objects.get_or_create(
                itemlot=instance.itemlot,
                location=instance.location,
                inventory_state=instance.inventory_state,
            )
            if item_inventory_lot.qty >= instance.qty:
                item_inventory_lot.qty -= instance.qty
                item_inventory_lot.save()
            else:
                raise ValidationError(_("Insufficient stock to decrease."))
        
        if created:
            # print the instance 
            print(f"ItemInvJournalEntry created: {instance}")
        
        pass



```


```python
# Create your models here.
import re
from django.db import models
from inventory.models import Item, ItemLot, unitofmeasure, unit, item_pricing_department,itemvariant,StockLotCostValuation,ItemInventoryLot
from addons.models import createdtimestamp_uid,discount
from party.models import Vendor, Staff,Client
from company.models import Company,Contact
from department.models import Branch
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from accounts.models import Charts_of_account, Transaction, Account,TransactionDoc,Tax
from django.db.models.signals import post_save, pre_save
from django.utils import timezone
from django.core.exceptions import ValidationError
from djmoney.money import Money
from djmoney.models.fields import MoneyField
from django.db import models


from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

# Create your models here.

####add an expiry transefer table for handling expiry


class TermsAndCondition(createdtimestamp_uid,models.Model):

    code = models.CharField(
        _("Terms and Condition Code"),
        max_length=10,
        help_text=_(
            "A code which uniquely identifies the condition for inventory being received, stored or shipped out by a retail store."
        ),
        unique=True,
    )
    decription = models.CharField(
        _("Description"), max_length=255, blank=True, null=True
    )
    # refundable = models.BooleanField(default=False, help_text="Is the product refundable?")
    exchangeable = models.BooleanField(default=False, help_text="Can the product be exchanged/buttered?")
    warranty_included = models.BooleanField(default=False, help_text="Does the product include a warranty?")
    defective_returns_allowed = models.BooleanField(default=False, help_text="Are defective returns allowed?")
    # restocking_fee_applicable = models.BooleanField(default=False, help_text="Is a restocking fee applicable?")
    delivery_insurance_provided = models.BooleanField(default=False, help_text="Is delivery insurance provided?")
    cod_allowed = models.BooleanField(default=False, help_text="Is cash on delivery allowed?")
    cancellation_policy_available = models.BooleanField(default=False, help_text="Is there a cancellation policy?")
    # international_shipping_available = models.BooleanField(default=False, help_text="Is international shipping available?")
    # restricted_item = models.BooleanField(default=False, help_text="Is the product subject to restrictions?")
    # bulk_purchase_discounts_available = models.BooleanField(default=False, help_text="Are bulk purchase discounts available?")
    # eco_friendly_packaging = models.BooleanField(default=False, help_text="Is eco-friendly packaging used?")
    # requires_age_verification = models.BooleanField(default=False, help_text="Is age verification required?")
    free_shipping_available = models.BooleanField(default=False, help_text="Is free shipping available?")
    return_window_days = models.PositiveIntegerField(
        default=0,
        help_text="Number of days in the return window. Set to 0 if returns are not allowed."
    )


    class Meta:
        verbose_name = _("TermsAndCondition")
        verbose_name_plural = _("TermsAndConditions")
    
    def save(self, *args, **kwargs):
        if self._state.adding:
            # generate a code for the terms and condition from the terms and coditions options
            pass
        return super(TermsAndCondition, self).save(*args, **kwargs)

    def __str__(self):
        return self.code

    def get_absolute_url(self):
        return reverse("TermsAndCondition_detail", kwargs={"pk": self.pk})

class InventoryCondition(createdtimestamp_uid, models.Model):

    name = models.CharField(
        _("Inventory Condition Code"),
        max_length=10,
        help_text=_(
            "A code which uniquely identifies the condition for inventory being received, stored or shipped out by a retail store. These codes will signify good, broken, damaged, wrong, partial shipment, overage, etc."
        ),
        unique=True,
    )
    description = models.CharField(
        _("Description"), max_length=255, blank=True, null=True
    )

    class Meta:
        verbose_name = _("InventoryCondition")
        verbose_name_plural = _("InventoryConditions")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("InventoryCondition_detail", kwargs={"pk": self.pk})



class Carrier(createdtimestamp_uid):
    
    name=models.CharField(_("Carrier"), max_length=50)
    description = models.CharField(
        _("Description"), max_length=255, blank=True, null=True
    )
    contact=models.ManyToManyField(Contact, verbose_name=_("Contact"),blank=True)

    carrieraccount=models.ForeignKey(
        Account,
        verbose_name=_("Carrier Accounts Payable"), 
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        editable=False,
        related_name="carrieraccount",
        limit_choices_to={"accounttype__name": "Accounts Payable"},
        )
    def save(self, *args, **kwargs):
        # if self._state.adding:
        #     accounttype,created = Charts_of_account.objects.get_or_create(
        #         name="Carrier Expense", company=self.company,
        #         description='Record all freight-related payments in this account.',
        #         account_type='Expenses',
        #         account_balance_type='Debit'
        #     )
        #     account,created=Account.objects.get_or_create(
        #         name=self.name,accounttype=accounttype, 
        #     )
        #     if created:
        #         self.account=account
        #     else:
        #         # raise validation error
        #         raise ValidationError("Account already exists")
        return super(Carrier, self).save(*args, **kwargs)

    
    class Meta:
        verbose_name = _("Carrier")
        verbose_name_plural = _("Carriers")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Carrier_detail", kwargs={"pk": self.pk})






class order_document(createdtimestamp_uid,):
    status = (
        ("pending", "pending"),
        ("approved", "approved"),
        ("fulfilled", "fulfilled"),
        ("canceled", "canceled"),
    )
    orderdoctype=(
        ("order_document", "Order Document"), # this is the base document for all orders
        ("purchase_order", "Purchase Order"),# supplier order
        ("sales_order", "Sales Order"),# customer order
        ("transfer_order", "Transfer Order"), # branch transfer order
        ("requisition_order", "Requisition Order"), # inventory requisition order
        ('adjustment_order', "Adjustment Order"), # inventory adjustment order
        ('return_order', "Return Order"), # supplier return order
    )
    ordertype = models.CharField(
        _("Order Type"), max_length=20, choices=orderdoctype, default="purchase_order"
    )
    title = models.CharField(
        _("Order Title"), max_length=150,
        help_text=_("A code which uniquely identifies the purchase order document.")
        # auto generated title
    )
    source_document = models.ForeignKey(
        'self',
        verbose_name=_("Source Document"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        # This way we can create multiple order documents from a single source document
    )
    status = models.CharField(
        _("Status"), max_length=15, choices=status, default="pending"
    )
    staff= models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        verbose_name=_("Staff"),
        null=True,
        blank=True,
    )
    branch = models.ForeignKey(
        Branch, verbose_name=_("Branch"), on_delete=models.CASCADE
    )
    order_amount=MoneyField(
        _("Order Amount"), max_digits=20, decimal_places=2,default=0,default_currency='GHS'
    )
    expected_delivery_date = models.DateTimeField(
        _("Expected Delivery Date"), blank=True, null=True
    )
    notes= models.TextField(
        _("Notes"), blank=True, null=True,
        help_text=_("Additional notes or comments regarding the order.")
    )
    # depending on the order type, the order document can be linked to a purchase order, sales order, transfer order, adjustment order or return order
    vendor = models.ForeignKey(
        Vendor, verbose_name=_("Selected Vendor"), null=True, blank=True, on_delete=models.CASCADE
    )
    client = models.ForeignKey(
        Client, verbose_name=_("Selected Client"), null=True, blank=True, on_delete=models.CASCADE
    )
    sourcebranch = models.ForeignKey(
        Branch, verbose_name=_("Source Branch"), null=True, blank=True, on_delete=models.CASCADE,related_name='source_branch_order'
    )


    def save(self, *args, **kwargs):
        if self._state.adding and not self.title:

            type_prefix = {
                "order_document": "OR",
                "purchase_order": "PO",
                "sales_order": "SO",
                "transfer_order": "TO",
                "adjustment_order": "AO",
                "return_order": "RO",
                # "requisition_order": "RO", # this is not used in the current implementation
            }.get(self.ordertype,'PO')
            count = order_document.objects.filter(
                created_at__date=timezone.now().date(),
                ordertype=self.ordertype,
                branch=self.branch
            ).count() + 1
            count_str = str(count).zfill(4)  # Pad with zeros to make it 4 digits
            self.title = f"{type_prefix}_{count_str}"
        return super(order_document, self).save(*args, **kwargs)

    def clean(self):
        # Ensure that the order type is valid
        if self.ordertype not in dict(self.orderdoctype).keys():
            raise ValidationError(_("Invalid order type selected."))
        # Ensure that the branch is set
        if not self.branch:
            raise ValidationError(_("Branch must be selected for the order document."))
        if self.ordertype=='sales_order' and self.client is None:
            raise ValidationError(_("Client must be selected for sales orders."))
        if self.ordertype in ['purchase_order', 'return_order'] and self.vendor is None:
            raise ValidationError(_("Vendor must be selected for purchase orders."))
        if self.ordertype=='transfer_order' and self.sourcebranch is None:
            raise ValidationError(_("Receiving branch must be selected for transfer orders."))
        if self.ordertype=='adjustment_order' and self.staff is None:
            raise ValidationError(_("Staff must be selected for adjustment orders."))
        if self.ordertype not in ['sales_order'] and self.staff is None:
            raise ValidationError(_("Staff User must be present for this order type."))
        return super().clean()
    class Meta:
        verbose_name = _("order_document")
        verbose_name_plural = _("order_documents")
        unique_together = ('title', 'branch', 'ordertype')

    def __str__(self):
        return f'{self.title}-{self.branch.name}'

    def get_absolute_url(self):
        return reverse("order_document_detail", kwargs={"pk": self.pk})



class order_document_attachment(createdtimestamp_uid, models.Model):

    order_document = models.ForeignKey(
        order_document, verbose_name=_("Order Document"), on_delete=models.CASCADE, related_name='attachments'
    )
    file = models.FileField(_("File"), upload_to='order_attachments/')
    # uploaded_at = models.DateTimeField(_("Uploaded sAt"), auto_now_add=True)

    class Meta:
        verbose_name = _("order_document_attachment")
        verbose_name_plural = _("order_document_attachments")

    def __str__(self):
        return self.file.name

    def get_absolute_url(self):
        return reverse("order_document_attachment_detail", kwargs={"pk": self.pk})



class order_document_detail(createdtimestamp_uid,models.Model):
    order= models.ForeignKey(
        order_document, verbose_name=_("Order Document"), on_delete=models.CASCADE, related_name='order_details'
    )
    item = models.ForeignKey(
        Item, verbose_name=_("Product"), on_delete=models.PROTECT
    )
    uom = models.ForeignKey(
        unitofmeasure, verbose_name=_("Unit of Measure"), on_delete=models.CASCADE
    )
    unit_cost_price = MoneyField(
        _("Cost Price per UOM"), max_digits=20, decimal_places=2,default=0,default_currency='GHS'
    )
    line_total = MoneyField(
        _("Unit Line Amount Price"),
        max_digits=25,
        decimal_places=2,default=0,default_currency='GHS',
        editable=False
    )
    qty = models.PositiveIntegerField(_("Order Qty"))
    qty_base = models.PositiveIntegerField(
        _("Received Qty in Base Unit"),editable=False
    )
    
    class Meta:
        verbose_name = _("order_document_detail")
        verbose_name_plural = _("order_document_details")

    def __str__(self):
        return f'{self.item.name} - {self.order.title}  - {self.qty}'
    def save(self, *args, **kwargs):
        self.qty_base = self.qty * self.uom.conversion_rate
        self.line_total = self.unit_cost_price * self.qty
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("order_document_detail_detail", kwargs={"pk": self.pk})




# This handles the transfer of products within a company
class TransferInventoryDocument(createdtimestamp_uid):
    # 
    line_number = models.PositiveIntegerField(_("Line Number"), default=1)
    transfer_number=models.CharField(
        _("Transfer Number"),
        max_length=150,
        help_text=_("A code which uniquely identifies the transfer document."), 
        editable=False
    )
    strict=models.BooleanField(
        _("Strict Transfer"),
        default=False,
        help_text=_("If true, items listed must be the same on both the in and out transfer details. Else, if there are variances(only less in than out allowed) create the reverse transfer"),
    )
    order_document=models.ManyToManyField(order_document, verbose_name=_("Order Document"), blank=True)
    # this allows for a transfer document to be created from a requisition document or from another transfer document
    # later on transfer documents must be linked to all types of documents including purchase orders and sales orders...
    #  meaning that a transfer document can be created from a purchase order or sales order
    in_branch = models.ForeignKey(
        Branch,
        verbose_name=_("Destination"),
        on_delete=models.CASCADE,
        related_name="in_destination_documents",
    )
    out_branch = models.ForeignKey(
        Branch,
        verbose_name=_("Source"),
        on_delete=models.CASCADE,
        related_name="out_source_documents",
    )
    return_inventory_document = models.ForeignKey(
        'self',
        verbose_name=_("Return From Transfer Document"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="transfer_inventory_documents",
    )
    is_return = models.BooleanField(_("Is Return Transfer"), default=False)
    in_notes = models.TextField(_("In Notes"), null=True, blank=True)
    out_notes = models.TextField(_("Out Notes"), null=True, blank=True)
    statuses = (
        ("pending", "pending"),
        ("transit", "transit"),
        ("cancel", "cancel"),
        ("accepted", "accepted"),
        ("partial_accept", "partial_accept"),
        ("rejected", "rejected"),
    )
    status = models.CharField(_("Status"), max_length=50, choices=statuses)
    delivery_staff = models.ForeignKey(
        Staff,
        verbose_name=_("Requested By"),
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name="transfer_delivery_person",
    )
    outcartoncount = models.PositiveIntegerField(
        _("Transfer Out Carton Count"),
        help_text=_("The number of cartons being transferred out."),
        default=0,
    )
    incartoncount = models.PositiveIntegerField(
        _("Transfer In Carton Count"),
        help_text=_("The number of cartons being transferred in."),
        default=0,
    )
    out_staff = models.ForeignKey(
        Staff,
        verbose_name=_("Out Staff By"),
        on_delete=models.CASCADE,
        related_name="transfer_out_staff",
    )
    in_staff = models.ForeignKey(
        Staff,
        verbose_name=_("In Staff By"),
        on_delete=models.CASCADE,
        related_name="transfer_in_staff",
        null=True,
        blank=True
    )

    transfer_in_stockvaluation=MoneyField(
        _("Stock Valuation In"),
        max_digits=20,
        decimal_places=2,
        default=0,
        default_currency='GHS',
        editable=False
    )
    transfer_out_stockvaluation=MoneyField(
        _("Stock Valuation Out"),
        max_digits=20,
        decimal_places=2,
        default=0,
        default_currency='GHS',
        editable=False
    )
    def clean(self):
        # Ensure that the in_branch and out_branch are not the same
        if self.in_branch == self.out_branch:
            raise ValidationError(
                _("The source and destination branches must be different.")
            )
        if self.is_return and self.return_inventory_document is None:
            raise ValidationError(
                _("Return transfer documents must reference the original transfer document.")
            )
        return super().clean()
    def save(self, *args, **kwargs):
        if self._state.adding:
            # generate a number for the transfer document
            self.line_number=TransferInventoryDocument.objects.all().count()+1
            self.transfer_number = self.generate_transfer_number()
        super(TransferInventoryDocument, self).save(*args, **kwargs)
    class Meta:
        verbose_name = _("Transfer Inventory Document")
        verbose_name_plural = _("Transfer Inventory Documents")
        unique_together = ("transfer_number", "in_branch","out_branch")
        permissions = [
            ("can_reverse_transfer", "Can reverse transfer"),
            ("can_cancel_transfer", "Can cancel transfer"),
            ("can_receive_transfer", "Can receive transfer"),
            ("can_reject_transfer", "Can reject transfer"),
            # ("can_void_bill", "Can void bill"),
            # ...
        ]
    def __str__(self):
        return self.transfer_number

    def get_absolute_url(self):
        return reverse("TransferInventoryDocument_detail", kwargs={"pk": self.pk})

    def generate_transfer_number(self):
        # generate a unique number for the transfer document
        count = TransferInventoryDocument.objects.filter(
            created_at__date=timezone.now().date(), in_branch=self.in_branch
        ).count() + 1
        count_str = str(count).zfill(4)
        # generate a number from the source and destination branches and the date and time of the transfer document
        return f"TR_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{count_str}"
    

class Transfer_Line_Item(createdtimestamp_uid):

    transferdoc = models.ForeignKey(
        TransferInventoryDocument,
        verbose_name=_("Transfer Document"),
        on_delete=models.CASCADE,
        related_name="transfer_line_items",
    )    
    line_number=models.PositiveSmallIntegerField(_("Line Number"),default=1,)
    item = models.ForeignKey(
        Item, verbose_name=_("Item"), on_delete=models.PROTECT,
    )
    transfer_order_details=models.ManyToManyField(
        order_document_detail,
        verbose_name=_("Order Document Detail"),
        blank=True,
    )
    in_amount_valuation = MoneyField(
        _("Total In Amount Price"),
        max_digits=25,
        decimal_places=2,default=0,default_currency='GHS',
    )
    out_amount_valuation = MoneyField(
        _("Total Out Amount Price"),
        max_digits=25,
        decimal_places=2,default=0,default_currency='GHS',
    )

    class Meta:
        verbose_name = _("Transfer_Line_Item")
        verbose_name_plural = _("Transfer_Line_Items")
        unique_together = ("transferdoc", "item")

    def __str__(self):
        return str(self.line_number)

    def get_absolute_url(self):
        return reverse("Transfer_Line_Item_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if self._state.adding and not self.line_number:
            self.line_number = Transfer_Line_Item.objects.filter(transferdoc=self.transferdoc).count() + 1
        super(Transfer_Line_Item, self).save(*args, **kwargs)

class OutTransfer(createdtimestamp_uid):
    line_number=models.PositiveSmallIntegerField(_("Line Number"),default=1)
    transfer_line_item = models.ForeignKey(
        Transfer_Line_Item,
        verbose_name=_("Transfer Line Item"),
        on_delete=models.CASCADE,
        related_name="out_transfer",
    )
    item_lot = models.ForeignKey(
        ItemLot,
        verbose_name=_("Lot"),
        on_delete=models.CASCADE,
    )

    condition = models.ForeignKey(
        InventoryCondition,
        verbose_name=_("Inventory Condition"),
        on_delete=models.CASCADE,
        related_name='+',
        null=True,
        blank=True
    )
    base_stock_valuation=MoneyField(
        _("Stock Cost Valuation"),
        max_digits=20,
        decimal_places=2,
        default_currency='GHS',
        null=True,
        blank=True
    )
    
    uom = models.ForeignKey(
        unitofmeasure, verbose_name=_("UOM"), on_delete=models.PROTECT,related_name="transfer_out_uom"
    )
    qty = models.PositiveIntegerField(_("Out Qty"),)
    base_qty = models.PositiveIntegerField(_("Out Base Qty"), editable=False)
    
    
    class Meta:
        verbose_name = _("OutTransfer")
        verbose_name_plural = _("OutTransfers")
        unique_together = ("transfer_line_item", "item_lot", "uom")

    def __str__(self):
        return str(self.line_number)
    
    def save(self, *args, **kwargs):
        if self._state.adding and not self.line_number:
            self.line_number = OutTransfer.objects.filter(transfer_line_item=self.transfer_line_item).count() + 1
        
        self.base_qty=  self.qty * self.uom.conversion_rate
        # self.base_qty = self.qty * self.uom.conversion_rate
        super(OutTransfer, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("OutTransfer_detail", kwargs={"pk": self.pk})

class OutTransferDetailVariant(createdtimestamp_uid):

    out_transfer= models.ForeignKey(OutTransfer, verbose_name=_("Out Transfer"), on_delete=models.CASCADE,
        related_name='out_transfer_variant'
    )
    variant=models.ForeignKey(itemvariant, verbose_name=_("Product Variant"), on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(
        _("Out Qty")
    )


    class Meta:
        verbose_name = _("OutTransferDetailVariant")
        verbose_name_plural = _("OutTransferDetailVariants")
        unique_together=('out_transfer','variant')

    def __str__(self):  
        return str(self.out_qty)

    def get_absolute_url(self):
        return reverse("OutTransferDetailVariant_detail", kwargs={"pk": self.pk})

class InTransfer(createdtimestamp_uid):

    # line_number=models.PositiveSmallIntegerField(_("Line Number"),default=1)
    out_transfer = models.OneToOneField(OutTransfer, verbose_name=_("Out Transfer"), on_delete=models.CASCADE,related_name='in_transfer')
    condition = models.ForeignKey(
        InventoryCondition,
        verbose_name=_("Inventory Condition"),
        on_delete=models.CASCADE,
        null=True,
        blank=True, 
        related_name='+',
    )
    uom = models.ForeignKey(
        unitofmeasure, verbose_name=_("UOM"), on_delete=models.CASCADE,related_name="transfer_in_uom"
    )
    qty = models.PositiveIntegerField(_("In Qty"))
    base_qty = models.PositiveIntegerField(_("In Base Qty"), editable=False, blank=True, null=True)
    class Meta:
        verbose_name = _("InTransfer")
        verbose_name_plural = _("InTransfers")
        # unique_together = ("out_transfer", "uom")

    def save(self, *args, **kwargs):
        self.base_qty = self.qty * self.uom.conversion_rate
        super(InTransfer, self).save(*args, **kwargs)
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse("InTransfer_detail", kwargs={"pk": self.pk})
    

class InTransferDetailVariant(createdtimestamp_uid):

    in_transfer= models.ForeignKey(InTransfer, verbose_name=_("In Transfer"), on_delete=models.CASCADE,
        related_name='in_transfer_variant'
    )
    variant=models.ForeignKey(itemvariant, verbose_name=_("Product Variant"), on_delete=models.CASCADE)
    in_qty = models.PositiveIntegerField(
        _("In Qty")
    )


    class Meta:
        verbose_name = _("InTransferDetailVariant")
        verbose_name_plural = _("InTransferDetailVariants")
        unique_together=('in_transfer','variant')

    def __str__(self):  
        return str(self.in_qty)

    def get_absolute_url(self):
        return reverse("InTransferDetailVariant_detail", kwargs={"pk": self.pk})

# class TransferInventoryDocumentDetail(createdtimestamp_uid):
#     detail = models.ForeignKey(
#         Transfer_Line_Item,
#         verbose_name=_("Transafer Line Item"),
#         on_delete=models.CASCADE,
#         related_name="transferdetail",
#     )
#     line_number=models.PositiveSmallIntegerField(_("Line Number"),default=1)
#     item_lot = models.ForeignKey(
#         ItemLot,
#         verbose_name=_("Item Lot Details"),
#         on_delete=models.PROTECT,
#     )
#     out_condition = models.ForeignKey(
#         InventoryCondition,
#         verbose_name=_("Out Inventory Condition"),
#         on_delete=models.CASCADE,
#         related_name='+',
#         null=True,
#         blank=True
#     )
#     uom_out = models.ForeignKey(
#         unitofmeasure, verbose_name=_("Transfer Out UOM"), on_delete=models.CASCADE,related_name="transfer_out_uom"
#     )
#     out_qty = models.PositiveIntegerField(_("Transferred Out Qty"))
#     in_condition = models.ForeignKey(
#         InventoryCondition,
#         verbose_name=_("In Inventory Condition"),
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True,
#         related_name='+',

#     )
#     uom_in = models.ForeignKey(
#         unitofmeasure, verbose_name=_("Transfer In UOM"), on_delete=models.CASCADE,related_name="transfer_in_uom"
#     )
#     in_qty = models.PositiveIntegerField(_("Approved In Qty"))

#     class Meta:
#         verbose_name = _("TransferInventoryDocumentDetail")
#         verbose_name_plural = _("TransferInventoryDocumentDetails")
#         unique_together = ("detail", "item_lot",)
#     def __str__(self):
#         return self.line_number
    
#     def save(self,*args, **kwargs):
#         if self._state.adding and not self.line_number:
#             self.line_number = TransferInventoryDocumentDetail.objects.filter(detail=self.detail).count() + 1

#         super(TransferInventoryDocumentDetail, self).save(*args, **kwargs)  # Call the real save() method


#     def get_absolute_url(self):
#         return reverse("TransferInventoryDocumentDetail_detail", kwargs={"pk": self.pk})


# vendor service  document
# class VendorServiceDocument(createdtimestamp_uid, models.Model):

# class TransferInventoryDocDetialVariant(createdtimestamp_uid):

#     transferinvdocdetail= models.ForeignKey(TransferInventoryDocumentDetail, verbose_name=_("Transfer Inventory Document Detail"), on_delete=models.CASCADE,
#     related_name='transfer_variant_dets'
#     )
#     variant=models.ForeignKey(itemvariant, verbose_name=_("Product Variant"), on_delete=models.CASCADE)
#     in_qty = models.PositiveIntegerField(
#         _("In Qty")
#     )
#     out_qty = models.PositiveIntegerField(
#         _("Out Qty")
#     )


#     class Meta:
#         verbose_name = _("TransferInventoryDocDetialVariant")
#         verbose_name_plural = _("TransferInventoryDocDetialVariants")
#         unique_together=('transferinvdocdetail','variant')

#     def __str__(self):  
#         return str(self.in_qty)

#     def get_absolute_url(self):
#         return reverse("TransferInventoryDocDetialVariant_detail", kwargs={"pk": self.pk})






class AdvancedShipNotice(createdtimestamp_uid):
    purchaseorders= models.ManyToManyField(
        order_document, verbose_name=_("Purchase Orders"),
        limit_choices_to={'ordertype': 'purchase_order'},
    )
    vendor = models.ForeignKey(
        Vendor, verbose_name=_("Vendor"), on_delete=models.CASCADE
    )
    termscondition = models.ForeignKey(TermsAndCondition, verbose_name=_("Terms and Conditions"), on_delete=models.CASCADE,null=True,blank=True)
    supplierexpectedshipdate = models.DateField(
        _("Supplier Expected Ship Date"), auto_now=False, auto_now_add=False, null=True, blank=True
    )
    supplieractualshipdate = models.DateTimeField(
        _("Supplier Actual Ship Date"), auto_now=False, auto_now_add=False,null=True, blank=True
    )
    expecteddeliverydate = models.DateField(
        _("Expected Delivery Date"), auto_now=False, auto_now_add=False,null=True, blank=True
    )
    serial_form_id = models.CharField(
        _("Serial Form ID"),
        max_length=50,
        help_text=_(
            "An idenfier for this document, usually preprinted on the form stock prior to being filled out."
        ),
    )
    class Meta:
        verbose_name = _("AdvancedShipNotice")
        verbose_name_plural = _("AdvancedShipNotices")
        unique_together = ("vendor", "serial_form_id")

    def __str__(self):
        return self.serialform_id

    def get_absolute_url(self):
        return reverse("AdvancedShipNotice_detail", kwargs={"pk": self.pk})


class packing_slip(models.Model):
    
    # A packing slip is a document that accompanies a shipment of goods and lists the items included in the shipment.
    # It is typically used to verify that the correct items have been shipped and received.
    # however the packing slip here is 
    asn = models.ForeignKey(
        AdvancedShipNotice, verbose_name=_("Advanced Ship Notice"), on_delete=models.CASCADE
    )
    purchaseorderdetails= models.ManyToManyField(
       order_document_detail, verbose_name=_("Purchase Order Details")
    )
    supplieritemname = models.CharField(
        _("Supplier Item Name"), max_length=100, blank=True, null=True
    )
    supplieritemcode = models.CharField(
        _("Supplier Item Code"), max_length=100, blank=True, null=True
    )
    supplierlotnumber = models.CharField(
        _("Supplier Lot Number"), max_length=100, blank=True, null=True
    )
    supplierexpirydate = models.DateField(
        _("Supplier Expiry Date"), auto_now=False, auto_now_add=False, null=True, blank=True
    )
    supplierquantity = models.PositiveIntegerField(
        _("Supplier Quantity"), default=0, help_text=_("Quantity of the item supplied")
    )
    supplieruom = models.ForeignKey(
        unitofmeasure, verbose_name=_("Supplier UOM"), on_delete=models.CASCADE
        # to be changed to a unit of measure model that is used by the supplier
    )
    supplierprice = MoneyField(
        _("Supplier Price"), max_digits=20, decimal_places=2, default=0,default_currency='GHS'
    )
    suppliertaxed = models.ManyToManyField(Tax, verbose_name=_("Taxes"), blank=True)
    supplierprice_taxincluded = MoneyField(
        _("Supplier Price (Tax Included)"), max_digits=20, decimal_places=2, default=0, default_currency='GHS'
    )

    class Meta:
        verbose_name = _("packing_slip")
        verbose_name_plural = _("packing_slips")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("packing_slip_detail", kwargs={"pk": self.pk})



class Bill(createdtimestamp_uid,discount,):
    # a bill is a representation of an invoice recieved from a supplier or a vendor detailing the amount owed by
    # the recipient of the bill for the purpose of supplying goods and or/ services. Improved on the invoice reciept
    # model with bill tracking for tracking bill amount, amount paid and amount due the bill
    # A bill indicates that the details on the billitem provided that it has been approved has been verified and is pending payment,
    # hence every bill is first posted to the stock account ledger and
    line_number=models.PositiveIntegerField(_("Line Number"),default=1, help_text=_("Line number for the bill item, this is auto generated"))
    billtype = (
        (
            "draft",#default state
            "draft",
        ),  # draft is pending completion and hence will not affect the stock ledger
        (
            "in_review",
            "in_review",
        ),  # bills that require additional review or approvals before approval,Does not affect the stock ledger
        (
            "canceled",
            "canceled",
        ),  # these have been rejected and do not affect the stock journal
        ('approved', 'approved'),  # these have been approved and are pending reciept/payment, these will affect the stock journal as the inventory may be pending reciept
        ("void", "void"),  
        # paid bill are those that have been rolled back completely... this means the inventory may be pending reciept however payment can be made for the bill and hence the supplier accout can be updated expecting 
        # bills that have been approved and are pending payment, these do not  affect the stock journal as the inventory may be pending reciept however payment can be made for the bill
        # approved bills can be sent to suppliers for supply (email or pdf format)  and payment can be made for the bill
        (
            'received',
            'received',
         # these have been recieved and are either pending/partial or completely paid for, these will affect the stock journal as the inventory has been received
        ),
            
    )
    paymenttermstype = (
        ("on_receipt", "Due On Reciept"),
        ('net_15', "Net 15 Days"),
        ("net_30", "Net 30 Days"),
        ("net_60", "Net 60 Days"),
        ("net_90", "Net 90 Days"),
        ("net_90+", "Net 90+ Days"),
    )
    billnumber = models.CharField(_("Purchase Invoice Number/Note"), max_length=100, help_text=_("A code which uniquely identifies the bill document."),editable=False)
    status = models.CharField(
        _("Bill status"), max_length=50, choices=billtype, default="draft"
    )
    order_document=models.ManyToManyField(order_document, verbose_name=_("Order Document"),
                                              limit_choices_to={'ordertype': 'purchase_order'},
                                              blank=True
                                              )
    
    paymentterms = models.CharField(
        _("Payment Terms"),
        max_length=50,
        choices=paymenttermstype,
        null=True,
        blank=True,
        help_text=_("Payment terms for the bill"),
    )
    paymenttermdate = models.DateField(
        _("Payment Due Date"), auto_now=False, auto_now_add=False,null=True, blank=True
    )
    vendor = models.ForeignKey(
        Vendor, verbose_name=_("Vendor"), on_delete=models.CASCADE
    )
    branch = models.ForeignKey(
        Branch, verbose_name=_("Branch"), on_delete=models.CASCADE
    )
    notes = models.TextField(_("Notes"), blank=True, null=True)
    staff=models.ForeignKey(
        Staff,
        verbose_name=_("Recieved by"),
        on_delete=models.CASCADE,
        related_name="staff_bill",
    )
    conversion_rate = models.DecimalField(
        _("Conversion Rate"),
        max_digits=20,
        decimal_places=6,
        default=1.0,
        help_text=_("Conversion rate for the bill currency to the base currency"),
    )

    billrecieptdate=models.DateTimeField(_("Recieved Date"), editable=False, auto_now=False, auto_now_add=False, blank=True, null=True)
    tax = models.ManyToManyField(
        Tax, verbose_name=_("Taxes"), blank=True, help_text=_("Taxes applied to the bill")
    )
    amount = MoneyField(_("Bill Amount"), max_digits=20, decimal_places=2,default=0,default_currency='GHS')
    subtotal_amount = MoneyField(_("Bill Amount(Cedis)"), max_digits=20, decimal_places=2,default=0,default_currency='GHS')
    discounted_amount = MoneyField(_("Discounted Amount"), max_digits=20, decimal_places=2,default=0,default_currency='GHS')
    tax_amount = MoneyField(_("Tax Amount Due(Cedis)"), max_digits=20, decimal_places=2,default=0,default_currency='GHS')
    total_amount = MoneyField(_("Total Amount(Cedis)"), max_digits=20, decimal_places=2,default=0,default_currency='GHS')

    # transaction=models.ForeignKey(TransactionDoc, verbose_name=_("Transaction Document"), on_delete=models.CASCADE,null=True, blank=True, editable=False)
    # this will link to the transaction document that records the bill item tra

    class Meta:
        verbose_name = _("Bill")
        verbose_name_plural = _("Bills")
        unique_together=("billnumber",'branch')
        permissions = [
            ("can_receive_bill", "Can receive bill"),
            ("can_void_bill", "Can void bill"),
            # ...
        ]

    def clean_paymentdate(self):
        # make sure that paymentterms and paymenttermdate are not null when billstatus is approved but pending reciept
        # if billtype is approved and paymentterms is not null make payment date a required field
        if self.status == "received" and (self.paymentterms is None or self.paymenttermdate is None):
            raise ValidationError("Payment Term and Date is required when the Bill is received")

    def clean(self):
        self.clean_discount()
        self.clean_paymentdate()
        return super().clean()
    

    def save(self, *args, **kwargs):
        # auto create the billnumber based on the bill invoice count +1 when adding new instamce 
        if self._state.adding:
            count=Bill.objects.filter(branch=self.branch).count()+1
            # prefix with bill with inv_ and suffix with count padded to 5 digits with date at the end
            self.line_number=count
            self.billnumber = f"INV_{count:05d}_{timezone.now().strftime('%Y%m%d')}"
        if self.status == "received":
            self.billrecieptdate = timezone.now()
        
        after_discount_amount = self.subtotal_amount-Money(self.discounted_amount.amount/self.conversion_rate,'GHS')

        self.total_amount = after_discount_amount + self.tax_amount
        # # amount
        # # subtotal_amount
        # # discounted_amount
        # # tax_amount

        # # total_amount
        print("Saving Bill: ",self.total_amount )
        print("Subtotal Amount: ",self.subtotal_amount )
        print("Discounted Amount: ",self.discounted_amount )
        print("Tax Amount: ",self.tax_amount )
        print("Conversion Rate: ",self.conversion_rate )
        print("After Discount Amount: ",after_discount_amount )
        super(Bill, self).save(*args, **kwargs)  # Call the real save() method

    def __str__(self):
        return self.billnumber

    def get_absolute_url(self):
        return reverse("Bill_detail", kwargs={"pk": self.pk})



class FreightBill(createdtimestamp_uid, models.Model):
    # A carrier-originated document that lists the number of containers (e.g. pallets, cartons, etc.) that were delivered to the store.
    # The freight bill does not reference the inner contents of a shipment. AKA Bill of Lading
    carrier = models.ForeignKey(
        Carrier, verbose_name=_("Carrier"), on_delete=models.CASCADE
    )
    invoicepicture = models.CharField(
        _("Invoice Picture"),
        max_length=50,
        help_text=_("A picture of the invoice or bill of lading."),
        null=True, blank =True
    )
    bill = models.ForeignKey(
        Bill, verbose_name=_("Bill"), on_delete=models.CASCADE, related_name="freightbill"
    )
    storecartoncount = models.PositiveIntegerField(
        _("Store Carton Count"),
        help_text=_("The number of cartons as established by the store."),
    )
    shippedcartoncount = models.PositiveIntegerField(
        _("Shipped Carton Count"),
        help_text=_("The number of cartons listed on the Freight Bill."),
    )
    conversion_rate = models.DecimalField(
        _("Conversion Rate"),
        max_digits=20,
        decimal_places=6,
        default=1.0,
    )
    cost = MoneyField(_("Freight Bill Cost"),default=0,default_currency='GHS', max_digits=15, decimal_places=2)
    class Meta:
        verbose_name = _("FreightBill")
        verbose_name_plural = _("FreightBills")
        unique_together=("carrier", "bill")


    def __str__(self):
        return self.bill.billnumber

    def get_absolute_url(self):
        return reverse("FreightBill_detail", kwargs={"pk": self.pk})



class Bill_Item(createdtimestamp_uid, models.Model):

    bill = models.ForeignKey(
        Bill,
        verbose_name=_("Bill"),
        on_delete=models.PROTECT,
        related_name="bill_items",
    )
    line_number=models.PositiveSmallIntegerField(_("Line Number"),default=1,)
    item = models.ForeignKey(
        Item, verbose_name=_("Product"), on_delete=models.PROTECT,
    )
    purchase_order_details=models.ManyToManyField(
        order_document_detail,
        verbose_name=_("Order Document Detail"),
        blank=True,
    )
    
    line_price = MoneyField(
        _("Total Unit Line Amount Price"),
        max_digits=25, 
        decimal_places=2,default=0,default_currency='GHS',
    )
    # qty_base = models.PositiveIntegerField(
    #     _("Actual Qty in Base Unit"),editable=False
    # )
    
    class Meta:
        verbose_name = _("Bill_Item")
        verbose_name_plural = _("Bill_Items")
        unique_together=('bill','item')
    
    def save(self, *args, **kwargs):
        if self._state.adding and not self.line_number:
            self.line_number=self.bill.bill_items.count()+1
        
        super().save(*args, **kwargs)

class BillDetail(createdtimestamp_uid,discount, models.Model):

    detail = models.ForeignKey(
        Bill_Item,
        verbose_name=_("Bill Item"),
        on_delete=models.PROTECT,
        related_name="billdetail",
    )
    line_number=models.PositiveSmallIntegerField(_("Line Number"),default=1)
    item_lot = models.ForeignKey(
        ItemLot,
        verbose_name=_("Item Lot Details"),
        on_delete=models.PROTECT,
    )
    uom = models.ForeignKey(
        unitofmeasure,
        verbose_name=_("Price Unit of Measure"),
        on_delete=models.CASCADE,
    )
    condition = models.ForeignKey(
        InventoryCondition,
        verbose_name=_("Condition Received"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    unit_cost_price = MoneyField(
        _("Cost Price per UOM"), max_digits=20, decimal_places=2,default=0,default_currency='GHS'
    )
    
    qty = models.PositiveIntegerField(
        _("Received Qty in Pack Size")
    )
    unit_cost_price_base= MoneyField(
        _("Cost Price per Base Unit"),editable=False, max_digits=20, decimal_places=2,default=0,default_currency='GHS'
    )
    qty_base = models.PositiveIntegerField(
        _("Received Qty in Base Unit"),editable=False
    )
    line_total = MoneyField(
        _("Unit Line Amount Price"),
        max_digits=25,
        decimal_places=2,default=0,default_currency='GHS',
        editable=False
    )
    # add an this object to StockLotCostValuation unit when the stock lot cost valuation is updated and 
    # the last billdetail that updated it

    def save(self, *args, **kwargs):
        self.qty_base=self.qty * self.uom.conversion_rate
        # check discount type and discount and calculate the discount and recalculate the line total
        self.line_total=self.unit_cost_price * self.qty
        if self.discount > 0:
            if self.discount_type == "percent":
                discount = self.line_total.amount * (self.discount)
                discount = Money(discount,self.line_total.currency)
            elif self.discount_type == "amount":
                if self.discount > self.line_total.amount:
                    # discount = self.line_total.amount
                    raise ValidationError("Discount cannot be greater than the line total")
                else:
                    discount = Money(self.discount,self.line_total.currency)
            self.line_total=Money(self.line_total.amount-discount.amount,self.line_total.currency)
        unitcost=Money(self.line_total.amount / self.qty_base,self.line_total.currency)
        self.unit_cost_price_base = unitcost
        # count the number of bill that have been created with the same bill and item
        # do this only if adding
        if self._state.adding and not self.line_number:
            self.line_number=self.detail.billdetail.count()+1
        # check if the product is a service and if so set the unit cost price to 0
        # raise ValidationError("Discount cannot be greater than the line total")
        
        super(BillDetail, self).save(*args, **kwargs)  # Call the real save() method

    class Meta:
        verbose_name = _("BillDetail")
        verbose_name_plural = _("BillDetails")
        unique_together=('detail','item_lot','uom')
    def __str__(self):
        return f"{self.line_number}"

    def get_absolute_url(self):
        return reverse("BillDetails_detail", kwargs={"pk": self.pk})
    
    def clean_prevent_service(self):
        # check if the product is a service and if so set the unit cost price to 0
        if self.product.is_service:
            # raisevalidation error
            raise ValidationError("Product is a service and cannot be returned")

    def clean_batches(self):
        # # check the status and if status is re if the product is a service and if so set the unit cost price to 0
        # if self.product.is_service:
        #     self.unit_cost_price = Money(0, self.unit_cost_price.currency)
        # return super().clean_batches()

        if self.item_lot is None and self.bill.status == 'received':
            raise ValidationError("Item Lot is required when the bill status is received")
        pass
    def clean(self):
        self.clean_batches()
        self.clean_prevent_service()
        self.clean_discount()
        return super().clean()
    

class BillDetailVariant(createdtimestamp_uid,models.Model):

    billdetail=models.ForeignKey(BillDetail, verbose_name=_("Bill Detail"), on_delete=models.CASCADE,related_name='billvariant')
    variant=models.ForeignKey(itemvariant, verbose_name=_("Product Variant"), on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(
        _("Received qty base form")
    )

    class Meta:
        verbose_name = _("BillDetailVariant")
        verbose_name_plural = _("BillDetailVariants")
        unique_together=('billdetail','variant')

    def clean_variant(self):
        # check if productvariant selected has the has product variants set to true and if not set to true
        
        # ensure that the product variant selected has the same product id as the product id of the billdetail 
        if self.variant.item.id != self.billdetail.item.id:
            raise ValidationError("Product variant selected does not match the product id of the billdetail")
        
        # check if the sum of the qty of all variants is equal to the sum of the qty of the base quantity on the billdetail
        # if self.qty != self.billdetail.qty_base:
        #     raise ValidationError("The sum of the qty of all variants is not equal to the sum of the qty of the base quantity on the billdetail")

    # self
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


    def clean(self):
        self.clean_variant()
        return super().clean()
    def __str__(self):
        return str(self.qty)

    def get_absolute_url(self):
        return reverse("billdetailvariant_detail", kwargs={"pk": self.pk})


class BillPayment(createdtimestamp_uid, models.Model):
    date = models.DateTimeField(_("Bill Payment Date"), auto_now=True)
    cash_account = models.ForeignKey(
        Account,
        verbose_name=_("Payment Account"),
        on_delete=models.CASCADE,
        related_name="paymentbillaccount",
    )
    vendoraccount = models.ForeignKey(
        Account,
        verbose_name=_("Vendor account"),
        on_delete=models.CASCADE,
        related_name="paymentrecieveaccount",
    )
    vendor=models.ForeignKey(Vendor, verbose_name=_("Vendor"), on_delete=models.CASCADE)
    bill = models.ForeignKey(
        Bill,
        verbose_name=_("Bill"),
        on_delete=models.CASCADE,
        related_name="billpayment",
    )
    payment_amount = models.DecimalField(
        _("Payment amount"), max_digits=5, decimal_places=2
    )

    notes = models.TextField(_("Payment Notes"))
    staff = models.ForeignKey(Staff, verbose_name=_("Staff"), on_delete=models.CASCADE)
    transaction=models.ForeignKey(TransactionDoc, verbose_name=_("Transaction Document"), on_delete=models.CASCADE)
    

    class Meta:
        verbose_name = _("BillPayment")
        verbose_name_plural = _("BillPayments")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("BillPayment_detail", kwargs={"pk": self.pk})


class ReturnReason(createdtimestamp_uid, models.Model):
    name = models.CharField(_("Return Reason"), max_length=100)
    description = models.TextField(_("Description"), blank=True, null=True)
    class Meta:
        verbose_name = _("Return Reason")
        verbose_name_plural = _("Return Reasons")

    def __str__(self):
        return self.name


class ReturnDocumentsupplier(createdtimestamp_uid):
        
    
    status = (
        ("pending", "pending"),
        ("approved", "approved"), #returns stock from state of on hand to on hold
        ("rejected", "rejected"), #returns stock from state of on hold to onhand
        ("returned", "returned"), #returns stock from state of on HOLD to on SUPPLIER(KEEP IN MIND THE COST PER UNIT ITEM IN THE BILL DETAIL)
    )
    staff = models.ForeignKey(
        Staff,
        verbose_name=_("Requested By"),
        on_delete=models.CASCADE,
    )
    
    statuscode = models.CharField(
        _("Status"), max_length=20, choices=status, default="pending"
    )
    reason =models.ForeignKey(ReturnReason, verbose_name=_("Return Reason"), on_delete=models.CASCADE, blank=True, null=True)
    source_document=models.ForeignKey(order_document, verbose_name=_("Source Document"), on_delete=models.CASCADE,null=True, blank=True, limit_choices_to={'status': 'approved', 'ordertype': 'return_order'})
    sourcebranch = models.ForeignKey(
        Branch,
        verbose_name=_("Return Branch"),
        on_delete=models.CASCADE,
    )
    returndate = models.DateField(_("Return date"), auto_now=False, auto_now_add=False)
    supplier = models.ForeignKey(
        Vendor, verbose_name=_("Supplier"), on_delete=models.CASCADE
    )
    bill = models.ForeignKey(Bill, verbose_name=_("Bill"), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("ReturnDocumentsupplier")
        verbose_name_plural = _("ReturnDocumentsuppliers")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("ReturnDocumentsupplier_detail", kwargs={"pk": self.pk})


class ReturnDocumentsupplierDetails(createdtimestamp_uid, models.Model):
    billdets = models.ForeignKey(
        BillDetail, verbose_name=_("Bill Details"), on_delete=models.CASCADE
    )
    document = models.ForeignKey(
        ReturnDocumentsupplier,
        verbose_name=_("Return Document"),
        on_delete=models.CASCADE,
        related_name="ReturnDocumentsupplier",
    )
    item = models.ForeignKey(
        Item, verbose_name=_("Product"), on_delete=models.PROTECT
    )
    lot = models.ForeignKey(ItemLot, verbose_name=_("Lots"), on_delete=models.CASCADE)
    
    uom = models.ForeignKey(
        unitofmeasure, verbose_name=_("Unit of Measure"), on_delete=models.CASCADE
    )

    qty = models.PositiveIntegerField(_("Qty"))
    qty_base = models.PositiveIntegerField(_("Qty Base"))

    class Meta:
        verbose_name = _("ReturnDocumentBranchDetails")
        verbose_name_plural = _("ReturnDocumentBranchDetailss")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("ReturnDocumentBranchDetails_detail", kwargs={"pk": self.pk})


class InventoryReconcilationEvent(createdtimestamp_uid):
    # This is a model to track inventory reconciliation events
    # It is used to track the events that lead to inventory reconciliation
    name = models.CharField(_("Name"), max_length=50)
    description = models.TextField(_("Description"), blank=True, null=True)

    class Meta:
        verbose_name = _("InventoryReconcilationEvent")
        verbose_name_plural = _("InventoryReconcilationEvents")

    def __str__(self):
        return self.name

class InventoryReconcilation(createdtimestamp_uid, models.Model):
    eventreason = models.ForeignKey(
        InventoryReconcilationEvent, verbose_name=_("Event Reason"), on_delete=models.CASCADE
    )
    branch = models.ForeignKey(
        Branch, verbose_name=_("Branch"), on_delete=models.CASCADE
    )
    source_document=models.ForeignKey(order_document, limit_choices_to={'status': 'approved', 'ordertype': 'adjustment_order'}, verbose_name=_("Source Document"), on_delete=models.CASCADE,null=True, blank=True)
    updatestock = models.BooleanField(_("Update stocks"))
    transactcount = models.PositiveIntegerField(_("Count"))
    notes = models.TextField(_("Notes"))

    class Meta:
        verbose_name = _("InventoryReconcilation")
        verbose_name_plural = _("InventoryReconcilations")
        unique_together=('eventreason','branch')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("InventoryReconcilation_detail", kwargs={"pk": self.pk})

class InventoryReconcilationItem(createdtimestamp_uid):

    item = models.ForeignKey(
        Item, verbose_name=_("Product"), on_delete=models.PROTECT
    )
    document = models.ForeignKey(
        InventoryReconcilation, verbose_name=_("Inventory Reconcilation"), on_delete=models.CASCADE,
        related_name="invreconitem",

    )
    line_number=models.PositiveSmallIntegerField(_("Line Number"),default=1,)

    class Meta:
        verbose_name = _("InventoryReconcilationItem")
        verbose_name_plural = _("InventoryReconcilationItems")
        unique_together = ('item','document')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("InventoryReconcilationItem_detail", kwargs={"pk": self.pk})


class InventoryReconcilationDetails(createdtimestamp_uid):
    status = (("increase", "increase"), ("decrease", "decrease"),("update", "update"))
    invreconitem = models.ForeignKey(
        InventoryReconcilationItem, verbose_name=_("Inventory Reconcilation Item"), on_delete=models.CASCADE,
        related_name="invreconitemdetails",
    )
    # invstate=models.ForeignKey(ItemInventoryLot, verbose_name=_("Inv Lot State"), on_delete=models.CASCADE)
    item_lot = models.ForeignKey(
        ItemLot,
        verbose_name=_("Lot"),
        on_delete=models.PROTECT,
    )
    direction = models.CharField(_("Direction"), max_length=50, choices=status,default='update')
    uom = models.ForeignKey(
        unitofmeasure, verbose_name=_("Unit of Measure"), on_delete=models.CASCADE
    )
    qty = models.PositiveIntegerField(_("Qty"))

    class Meta:
        verbose_name = _("InventoryReconcilationDetails")
        verbose_name_plural = _("InventoryReconcilationDetailss")
        unique_together = ('invreconitem','item_lot','uom')
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("InventoryReconcilationDetails_detail", kwargs={"pk": self.pk})

class InventoryReconcilationItemVariant(createdtimestamp_uid):
    
    recondetail= models.ForeignKey(InventoryReconcilationDetails, verbose_name=_("Transfer Inventory Document Detail"), on_delete=models.CASCADE,
    related_name='inv_reconc_detail_variant_details'
    )
    variant=models.ForeignKey(itemvariant, verbose_name=_("Product Variant"), on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(
        _("qty base")
    )

    class Meta:
        verbose_name = _("InventoryReconcilationItemVariant")
        verbose_name_plural = _("InventoryReconcilationItemVariants")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("InventoryReconcilationItemVariant_detail", kwargs={"pk": self.pk})


class SupplierItem(createdtimestamp_uid):
    supplier = models.ForeignKey(
        Vendor, verbose_name=_("Supplier"), on_delete=models.CASCADE
    )
    item = models.ForeignKey(Item, verbose_name=_("Product"), on_delete=models.CASCADE)
    # Supplier item name is the name of the item as it appears on the supplier's catalog
    name = models.CharField(
        _("Supplier Item Name"), max_length=100, blank=True, null=True
    )
    # AvailabilityStatus = models.BooleanField(_("Supplier Has stocks")) # this is to be moved to the supplier order response model
    moq = models.PositiveIntegerField(
        _("Supplier Minimum Order Quantity (Packs)"),
        blank=True,
        null=True,
    )
    uom = models.ForeignKey(
        unitofmeasure,
        verbose_name=_("Unit Of Measure"),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("SupplierItem")
        verbose_name_plural = _("SupplierItems")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("SupplierItem_detail", kwargs={"pk": self.pk})


```


```python

from django.db import models
from inventory.models import Item,ItemLot, unitofmeasure,StockLotCostValuation,ItemInventoryLot
from department.models import Department, Branch
from django.utils.translation import gettext_lazy as _
import re
from invplan.models import order_document
from django.urls import reverse
from djmoney.models.fields import MoneyField
from party.models import User,Staff
from addons.models import createtimstam_uid
# Create your models here.
# this module defines manufacturing related models such as WorkOrder, BillOfMaterials, ProductionLine, etc.
# these models will be used to manage and track manufacturing processes within the ERP system.
# further implementation will include fields, methods, and relationships relevant to manufacturing operations.
# this is a placeholder for future development.
# https://deepwiki.com/frappe/erpnext/6-manufacturing
# https://deepwiki.com/OCA/manufacture/1-overview




class BillOfMaterials(createtimstam_uid):
    items=models.ForeignKey(Item,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(_("Quantity"))
    uom=models.ForeignKey(unitofmeasure,on_delete=models.CASCADE)
    department=models.ForeignKey(Department,on_delete=models.CASCADE)
    status=models.BooleanField(default=True)
    is_default=models.BooleanField(default=False)
    # variants=models.ManyToManyField(ItemVariantType,blank=True)
    # this  allows you to create multiple variants of a product with different attributes
    service_charge=MoneyField(_('Service Charge'),
        max_digits=14,
        decimal_places=2,
        default=0,
        default_currency='GHS'
    )
    # unique constraint to ensure one default BOM per item
    # class Meta:
    #     unique_together = ('items', 'is_default')
    created_by=models.ForeignKey(Staff,on_delete=models.SET_NULL,null=True,related_name='bom_created_by')
    modified_by=models.ForeignKey(Staff,on_delete=models.SET_NULL,null=True,related_name='bom_modified_by')
    formulation_details=models.TextField(blank=True,null=True)

    def __str__(self):
        return f"{self.items.name} - {self.quantity} {self.uom.name} "

    def get_absolute_url(self):
        return reverse("BillOfMaterials_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        # Ensure only one default BOM per item
        if self.is_default:
            BillOfMaterials.objects.filter(items=self.items).update(is_default=False)
        super().save(*args, **kwargs)


class BillOfMaterialsItems(createtimstam_uid):
    items=models.ForeignKey(Item,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(_("Quantity"))
    uom=models.ForeignKey(unitofmeasure,on_delete=models.CASCADE)
    bom=models.ForeignKey(BillOfMaterials,on_delete=models.CASCADE,related_name='bom_items'
    )
    service_charge=MoneyField(_('Service Charge'),
        max_digits=14,
        decimal_places=2,
        default=0,
        default_currency='GHS'
    )

    def __str__(self):
        return f"{self.items.name} - {self.quantity} {self.uom.name} "
    def get_absolute_url(self):
        return reverse("BillOfMaterialsItems_detail", kwargs={"pk": self.pk})



class Machinery(createtimstam_uid):
    name=models.CharField(max_length=200)
    description=models.TextField(blank=True,null=True)
    department=models.ForeignKey(Department,on_delete=models.CASCADE)
    status=models.CharField(max_length=100,default='operational', choices=(
        ('operational','Operational'),
        ('under_maintenance','Under Maintenance'),
        ('out_of_order','Out of Order'),
    )
    )
    pass


# Production Line Model
# This model represents a production line within the manufacturing facility.
# This includes details such as line name, capacity, assigned machines, and status.



class ProductionLine(createtimstam_uid):
    #


    pass

class ManufacturingBatch(createtimstam_uid):
    
    pass



class MaintenanceSchedule(createtimstam_uid):
    # cost of ma
    pass

class QualityCheck(models.Model):
    
    pass

class Shift(models.Model):
    
    pass

class Labor(models.Model):
    
    pass

class RawMaterialRequirement(models.Model):
    
    pass

class FinishedProduct(models.Model):
    
    pass

class ProductionSchedule(models.Model):
    
    pass

class InventoryAdjustment(models.Model):
    
    pass


class ScrapRecord(models.Model):
    
    pass


class ManufacturingCost(models.Model):
    
    pass



```


```python

from typing import Iterable
from django.db import models
from django.contrib.auth.models import AbstractUser
from company.models import Company,PaymentClass,Contact
from department.models import Branch, Department
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from testdummy.dummyvaluescreator import generate_random_names
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from accounts.models import Account, Charts_of_account
# from autoslug import AutoSlugField
from addons.models import createdtimestamp_uid, phonenumberMixin,socialmedMixin,activearchlockedMixin,addressMixin,CompanyMixin
from contact.models import Phone,Address,Email,Website,Country,City,State
# Create your models here.
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.models import Group,Permission
from djmoney.models.fields import MoneyField




class Occupation(createdtimestamp_uid):

    name = models.CharField(_("Occupation"), max_length=200)
    definition = models.TextField(_("Definition"), blank=True, null=True)
    task=models.TextField(_("Tasks"),blank=True, null=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    class Meta:
        verbose_name = _("Occupation")
        verbose_name_plural = _("Occupations")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Occupation_detail", kwargs={"pk": self.pk})

AUTH_PROVIDERS = {'facebook': 'facebook', 'google': 'google',
                  'twitter': 'twitter', 'email': 'email','base_auth':'base_auth'}

class User(createdtimestamp_uid, AbstractUser):
    is_admin = models.BooleanField(_("Is Admin User"), default=False)
    is_client = models.BooleanField(_("Is Client"), default=False)
    is_vendor = models.BooleanField(_("Is Vendor"), default=False)
    company=models.ForeignKey(Company, verbose_name=_("Company"), on_delete=models.CASCADE,blank=True, null=True)
    # choicedusertypes=(
    #     ('Admin','Admin'),
    #     ('Staff','Staff'),
    #     ('Client','Client'),
    #     ('Vendor','Vendor'),
    # )
    # usertype=models.CharField(_("User Type"), max_length=15,choices=choicedusertypes,blank=True, null=True)
    # company should only be associated with staff users 
    # company to be removed from this model
    # and vendor are simply companies registered with the project
    # and customers have freedom to choose which companies they work with
    # Change so that the perspective is right
    # associationtype=models.ForeignKey(associationtype, verbose_name=_("Vendor Association Type"), on_delete=models.CASCADE,blank=True, null=True,)
    # association=models.ForeignKey("self", verbose_name=_("Association"), on_delete=models.CASCADE,blank=True, null=True,)
    is_verified=models.BooleanField(_("Is Verified?"),default=False)
    auth_provider = models.CharField(
        max_length=255, blank=False,
        null=False, default=AUTH_PROVIDERS.get('base_auth'))
    # email = models.EmailField(max_length=255, unique=True, db_index=True)
    # is_verified = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        if self.company is None and not self.is_superuser:
            raise ValidationError(
                "All users must belong to the company to which they are employed."
            )
        # if self.email:
            # get or create email from email table
        if self._state.adding:
            if self.is_superuser:
                load_base_init_data()
                self.is_admin = True
                self.is_staff=True
                self.is_verified=True
                # this will be deleted before production
                paymentclass, created=PaymentClass.objects.get_or_create(
                    name="Cash",
                )

                country=Country.objects.get(name='Ghana')
                comp,created=Company.objects.get_or_create(
                    name="Test Company",
                    payment=paymentclass,
                    is_active=True,
                    tradecountry=country
                )
                
                self.company=comp
                # staff,created=Staff.objects.get_or_create(
                #     staff=self.id,
                #     company=comp,
                #     # is_active=True,
                #     managerial_status=True
                # )
        super(User, self).save(*args, **kwargs)

        # if self.is_client:
        #     self.is_superuser=False
        #     self.is_admin =  False
        #     self.is_staff =  False
        #     self.is_vendor=  False
        # elif self.is_vendor:
        #     self.is_admin = False
        #     self.is_staff=  False
        #     self.is_client= False
        #     self.is_superuser=False
        # elif self.is_staff:
        #     pass
        # else:
        #     self.is_admin = False
        #     self.is_staff=  False
        #     self.is_vendor=  False
        #     self.is_client=False
        #     self.is_superuser=False
        #     self.is_active=False
        # else:
        #     pass
        # if a user does not belong to a company and also does not have 
        # staffuser status set then the user is automatically a customer
        
        # raise ValidationError("All users must belong to the company")

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def get_absolute_url(self):
        return reverse("User_detail", kwargs={"pk": self.pk})

from testdummy.dummyvaluescreator import generate_secure_pin
class PasswordReset(createdtimestamp_uid):
    email = models.EmailField()
    token = models.CharField(max_length=100,unique=True)
    # pin=models.CharField(_("pin"), max_length=5,default=generate_secure_pin())
    is_active = models.BooleanField(_("Is Active"), default=False)


    def save(self, *args, **kwargs):
        # check if email exists in the user model
        if self.email and User.objects.filter(email=self.email).exists():
            super(PasswordReset, self).save(*args, **kwargs)


def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        # update this code
        if instance.is_superuser or instance.is_staff:
            staff,created=Staff.objects.get_or_create(
                staff=instance,
                managerial_status=instance.is_superuser

            )
        # elif instance.is_staff:
        #     staff, created = Staff.objects.get_or_create(
        #         staff=instance,
        #         managerial_status=False
        #     )
        else:
            pass
post_save.connect(create_profile, sender=User)






class id_type(createdtimestamp_uid):

    name= models.CharField(_("Name"), max_length=50, )

    class Meta:
        verbose_name = _("id_type")
        verbose_name_plural = _("id_types")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("id_type_detail", kwargs={"pk": self.pk})
class religion(createdtimestamp_uid):

    name= models.CharField(_("Religion"), max_length=50, unique=True)

    class Meta:
        verbose_name = _("religion")
        verbose_name_plural = _("religions")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("religion_detail", kwargs={"pk": self.pk})


class Profile(createdtimestamp_uid, models.Model):
    id = None
    GENDER_CHOICES = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Prefer_Not_to_Say", "Prefer_Not_to_Say"),
        ("Non_Binary", "Non_Binary"),
        ("Transgender", "Transgender"), 
        ("Intersex", "Intersex"),
        ("Genderqueer", "Genderqueer"),
        ("Agender", "Agender"),
        ("Pangender", "Pangender"),
        ("Two_Spirit", "Two_Spirit"),
        ("Bigender", "Bigender"),
        ("Genderfluid", "Genderfluid"),
        ("Other", "Other"),
    )
    EMPLOYMENT_STATUS_CHOICES = (
        ("Employed", "Employed"),
        ("Unemployed", "Unemployed"),
        ("Student", "Student"),
        ("Semi_Retired", "Semi_Retired"),
        ("Retired", "Retired"),
        ("Self_Employed", "Self_Employed"),
        ("Part_Time_Employment", "Part_Time_Employment"),
    )
    EDUCATIONAL_LEVEL_CHOICES = (
        ("Primary","Primary"),
        ("Secondary","Secondary"),
        ("Tertiary","Tertiary"),
        ("Post_Graduate","Post_Graduate"),
        ("Doctorate","Doctorate"),
        ("None","None"),
    )
    
    MARITAL_STATUS = [
        ("Single", "Single"),
        ("Married", "Married"),
        ("Divorced", "Divorced"),
        ('Widowed','Widowed'),
        ('Separated','Separated'),
    ]

    user = models.OneToOneField(
        User,
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="profile",
    )
    # picture = models.ImageField(
    #     _("Profile Picture"),blank=True, null=True
    # )
    profile_picture = models.CharField(
        _("Profile Picture URL"), max_length=100, blank=True, null=True
    )
    date_of_death = models.DateField(null=True, blank=True)

    # bioimage = models.ImageField(
    #     _("Bio Image"), upload_to='bioimages/', blank=True, null=True
    # )
    bioimage= models.CharField(
        _("Bio Image URL"), max_length=100, blank=True, null=True
    )
    # bio = models.TextField(max_length=500, blank=True)
    education_level_code = models.CharField(
        _("Highest Educational Level Completed"),
        choices=EDUCATIONAL_LEVEL_CHOICES,
        max_length=50,
        default="None"
    )
    birth_date = models.DateField(null=True, blank=True)
    employment_status = models.CharField(

        _("Current Employment Status"), max_length=50, choices=EMPLOYMENT_STATUS_CHOICES,default="Unemployed", 
    )
    gender = models.CharField(
        _("Gender"), max_length=50, choices=GENDER_CHOICES, default="Male"
    )

    marital_status = models.CharField(
        _("Marital Status"),
        max_length=50,
        choices=MARITAL_STATUS,
        default="Single",
    )
    occupation = models.ManyToManyField(
        Occupation, verbose_name=_("Occupation"), blank=True
    )
    religion=models.ForeignKey(
        religion, verbose_name=_("Religion"), on_delete=models.SET_NULL, blank=True, null=True
    )
    # to be updated to just a contact field
    contact=models.ManyToManyField(Contact, verbose_name=_("Contact"),blank=True)
    # add allergies
    # foodalergies=models.ManyToManyField(Foodallergy, verbose_name=_("Food Allergy"),blank=True)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        super(Profile, self).save(*args, **kwargs)

    class Meta:
        permissions = [
            ("can_view_other_profile", "Can view other profile"),
            ("can_edit_other_profile", "Can edit other profile"),
            # ...
        ]


class national(createdtimestamp_uid):
    user=models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    id_type=models.ForeignKey(id_type, verbose_name=_("Id Type"), on_delete=models.CASCADE)
    national_id=models.CharField(_("National Id"), max_length=50, null=False,blank=False)

    class Meta:
        verbose_name = _("national")
        verbose_name_plural = _("nationals")
        unique_together=('user','id_type','national_id')

    def __str__(self):
        return self.national_id

    def get_absolute_url(self):
        return reverse("national_detail", kwargs={"pk": self.pk})



class ClientGroup(createdtimestamp_uid, models.Model):
    company = models.ForeignKey(
        Company, verbose_name=_("Company"), on_delete=models.CASCADE
    )
    
    name = models.CharField(_("Client Group"), max_length=50)
    description = models.CharField(
        _("Brief Description of Client Group"), max_length=255, blank=True, null=True
    )

    class Meta:
        verbose_name = _("Client Group")
        verbose_name_plural = _("Client Groups")
        unique_together=('company','name')
        

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("CustomerGroup_detail", kwargs={"pk": self.pk})


class StaffGroup(createdtimestamp_uid, models.Model):
    company = models.ForeignKey(
        Company, verbose_name=_("Company"), on_delete=models.CASCADE
    )
    name = models.CharField(_("Staff Group"), max_length=50)
    description = models.CharField(
        _("Brief Description of Staff Group"), max_length=255, blank=True, null=True
    )
    # permissions=models.ManyToManyField(permissions, verbose_name=_("Group Perm"))
    is_an_associate_group_of = models.ForeignKey(
        "self",
        verbose_name=_("Is an associate of"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _("Staff Group")
        verbose_name_plural = _("Staff Groups")
        unique_together=('company','name')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("StaffGroup_detail", kwargs={"pk": self.pk})


class Staff(createdtimestamp_uid,  models.Model):
    id = None
    # STAFF_CATEG = (("wholesaler", "Wholesaler "),("retailer", "Retailer"),("manufacturing", "Manufacturing"),("warehouse_distribution","Warehouse_Distribution",),)
    staff = models.OneToOneField(
        User,
        verbose_name=_("Staff"),
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
        related_name="staffing",
        primary_key=True,
    )
    # unique=True
    contact=models.ManyToManyField(Contact, verbose_name=_("Contact"),blank=True)

    staffgroup = models.ForeignKey(
        StaffGroup,
        verbose_name=_("Staff Group"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    choicestatus=(
        ('archived','archived'),
        ('locked','locked'),
        ('deleted','deleted'),
        ('active','active')
    )
    status=models.CharField(_("Status"),choices=choicestatus,default='active', max_length=50)
    
    # reconsider  making this a part of the hr section
    # is_administrative=models.BooleanField(_("Is Administrative Staff"))
    # all staff must belong to atleast a department... and have a permission and permission group
    departments=models.ManyToManyField(Department, verbose_name=_("Department"),related_name='staffdepartment',blank=True, editable=False) # to be made required
    branch=models.ManyToManyField(Branch, verbose_name=_("Branch"),related_name="staffbranch",blank=True)
    managerial_status = models.BooleanField(_("Is_manager"), default=False)
    managed_by = models.ForeignKey(
        "self",
        verbose_name=_("Manager(Reports to)"),
        on_delete=models.CASCADE,
        limit_choices_to={"managerial_status": True},
        blank=True,
        null=True,
        related_name="Manager",
    )
    # accounts=models.ManyToManyField(Account, verbose_name=_("Accounts"), blank=True, related_name="staffaccounts")
    staffaccount = models.ForeignKey(
        Account,
        verbose_name=_("StaffAccount"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        editable=False,
        related_name="staffaccount",
        limit_choices_to={"accounttype__name": "Payroll Expenses"},
    )
    # # create an account for when staff buys on credit sale
    credit_sale_account = models.ForeignKey(
        Account,
        verbose_name=_("Credit Sale Account"),
        on_delete=models.CASCADE,
        blank=True,
        editable=False,
        null=True,
        related_name="credit_staffaccount",
        limit_choices_to={"accounttype__name": "Accounts Receivables"},
        # should be notes receivable 
    )
    # and maybe staff accounts should be a multiple account field so that staff can have multiple accounts for different purposes and transactions
    class Meta:
        verbose_name = _("staff")
        verbose_name_plural = _("staffs")
        permissions = [
            (
                "can_switch_branch",
                "Can change swhitch branch a pallet is stored in"
            )
        ]

    def save(self, *args, **kwargs):
        # set department from branch
        # if self.branch.exists():
        #     self.departments.set(self.branch.department.all())
        departments=[branch.department for branch in self.branch.all()]
        self.departments.set(departments)
        return super(Staff, self).save(*args, **kwargs)

    def __str__(self):
        return self.staff.username

    def get_absolute_url(self):
        return reverse("staff_detail", kwargs={"pk": self.staff.pk})



class Client(createdtimestamp_uid, models.Model):
    # name=models.CharField(_("Customer Name"), max_length=60)
    id=None
    department = models.ForeignKey(
        Department, verbose_name=_("Client Department"),
        on_delete=models.DO_NOTHING,
        related_name='clientdepartment',
        limit_choices_to={
            'status': 'active',
            'is_saledepartment':True,}
        )
    is_organization = models.BooleanField(
        _("Is the Client an Organization"), default=False
    )
    user = models.OneToOneField(
        User,
        primary_key=True,
        verbose_name=_("Client User"),
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff":False,'is_client':True},
        related_name='userclient',
    )
    # customer user preferences 
    # customer
    preferences = models.ManyToManyField("preference", blank=True)
    # Create an api for assigning users to this model if user is not set
    client_group = models.ForeignKey(
        ClientGroup,
        verbose_name=_("Client Group"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    choicestatus=(
        ('archived','archived'),
        ('locked','locked'),
        ('deleted','deleted'),
        ('active','active')
    )
    status=models.CharField(_("Status"),choices=choicestatus,default='active', max_length=50)
    expiration_date = models.DateField(_("Expiration Date"), blank=True, null=True)
    client_account = models.ForeignKey(
        Account,
        verbose_name=_("Client Account"),
        on_delete=models.CASCADE,
        limit_choices_to={"accounttype__name": "Accounts Receivables"},
        related_name="cusaccount",
        editable=False,
        null=True,
        blank=True
    )
    contact=models.ManyToManyField(Contact, verbose_name=_("Contact"),blank=True)
    
    is_creditsale_allowed=models.BooleanField(_("Is Credit Sale Allowed"),default=False)
    # This customer can not make credit sales
    parents = models.ManyToManyField('self', symmetrical=False, related_name='children', blank=True,
        help_text="Select biological parents only. This field is used to establish family relationships for medical history and contact purposes."
    )


    # Parents are available as self.parents.all()

    # def siblings(self):
    #     # Siblings: people who share at least one parent, excluding self
    #     return Client.objects.filter(parents__in=self.parents.all()).exclude(user_id=self.user.id).distinct()

    # def full_siblings(self):
    #     # Full siblings: share the exact same set of parents
    #     return Client.objects.filter(
    #         parents__in=self.parents.all()
    #     ).annotate(
    #         num_parents=models.Count('parents')
    #     ).filter(
    #         num_parents=self.parents.count()
    #     ).exclude(user_id=self.user.id).distinct()

    # def half_siblings(self):
    #     # Half siblings: share only one parent, not all
    #     return self.siblings().exclude(pk=self.full_siblings())

    # def first_cousins(self):
    #     # First cousins: children of your parents' siblings (aunts/uncles)
    #     parent_siblings = Client.objects.filter(parents__in=self.parents.values('parents')).exclude(user_id=self.parents.values('user_id'))
    #     return Client.objects.filter(parents__in=parent_siblings).exclude(user_id=self.user.id).distinct()

    # def second_cousins(self):
    #     # Second cousins: children of your parents' cousins
    #     first_cousins = self.first_cousins()
    #     cousins_children = Client.objects.filter(parents__in=first_cousins)
    #     return cousins_children.exclude(user_id=self.user.id).distinct()
    
    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        # unique_together=('name','customerdepartment')

    def __str__(self):
        return self.user.username

    def get_absolute_url(self):
        return reverse("Customer_detail", kwargs={"pk": self.pk})

    # 
    # write a function and define customer_account_type based on the customer account type based on a customers interaction with the company
    # 
    # customer_account_choice = (
    #     ("New", "New"),
    #     ("Loyalty", "Loyalty"),
    #     ("Rebate", "Rebate"),
    #     ("Regular", "Regular"),
    #     ("Trade", "Trade"),
    #     ("Installment", "Installment"),
    # )
    # def customer_account_type(self):
    # 
    

    def save(self, *args, **kwargs):
        
        if self.user:
            self.name = self.user.username
        super(Client, self).save(*args, **kwargs)  # Call the real save() method

# vendor is a company that provides goods or services to another company
# vendor relationships are to be defined by the company and not by the vendor
class Vendor(createdtimestamp_uid):
    vendtype = (
        ("ServiceProvider", "ServiceProvider"),
        ("Manufacturer", "Manufacturer"),
        ("Supplier", "Supplier"),
    )
    choicestatus=(
        ('archived','archived'),
        ('locked','locked'),
        ('deleted','deleted'),
        ('active','active')
    )
    status=models.CharField(_("Status"),choices=choicestatus,default='active', max_length=50)
    vendoraccount = models.OneToOneField(
        Account,
        verbose_name=_("Vendor Account"),
        on_delete=models.CASCADE,
        limit_choices_to={"accounttype__name": "Accounts Payable"},
        null=True,
        blank=True,
        editable=False
    )
    vendorname = models.CharField(_("Vendor Name"), max_length=150,unique=True,blank=False, null=False)
    vendortype = models.CharField(
        _("Vendor Type"), max_length=50, choices=vendtype, default="Supplier"
    )
    company = models.ForeignKey(
        Company, verbose_name=_("Company"), on_delete=models.CASCADE
    )
    user = models.OneToOneField(
        User,
        verbose_name=_("Vendor"),
        on_delete=models.CASCADE,
        limit_choices_to={
            "is_vendor": True,
        },
        blank=True,
        null=True,
        editable=False,
        help_text=_(
            "A Person from whom the retail enterprise may purchase goods or services."
        ),
        related_name='vendoruser'
    )
    staff=models.ForeignKey(User, verbose_name=_("Staff"), on_delete=models.DO_NOTHING,editable=False)
    # change assigning vendors to users to assigning vendors to a company
    # Create an api for assigning users to this model if user is not set
    contact=models.ManyToManyField(Contact, verbose_name=_("Contact"),blank=True)
    class Meta:
        verbose_name = _("Vendor")
        verbose_name_plural = _("Vendors")
        unique_together=('company','vendorname')
        

    def __str__(self):
        return self.vendorname


    def clean(self):
        return super().clean()

    def save(self, *args, **kwargs):
        if self.user:
            self.vendorname = self.user.username
        super(Vendor, self).save(*args, **kwargs)  # Call the real save() method
        

# def update_vendor(sender, instance, created, **kwargs):
#     if created:
#         accounttype = Charts_of_account.objects.get(
#             name="Accounts Payable", company=instance.company
#         )
#         vendoracc = Account.objects.create(
#             name=instance.id,
#             accounttype=accounttype,
#         )
#         instance.vendoraccount = vendoracc
#         instance.save()

# post_save.connect(update_vendor, sender=Vendor)




# same format for drug drug interactions and others
class preference(createdtimestamp_uid):
    ALLOWED_MODELS = ['itemvariant', 'VariantAttribute', 'Manufacturer', 'ProductsCategory']
    # company=models.ForeignKey(Company, verbose_name=_("Company"), on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    preference_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return f"{self.content_type.model}: {self.preference_object}"


    class Meta:
        verbose_name = _("preference")
        verbose_name_plural = _("preferences")
        # unique_together=('company',  'content_type', 'object_id')

    def clean(self):
        self.cleanex()
        return super().clean()
    
    def cleanex(self):
        if self.content_type.model not in self.ALLOWED_MODELS:
            raise ValidationError(f"Invalid preference type: {self.content_type.model}")
        pass


    def get_absolute_url(self):
        return reverse("prefernces_detail", kwargs={"pk": self.pk})


from inventory.models import itemvariant,VariantAttribute,Manufacturer,Category
@receiver(post_save, sender=itemvariant)
@receiver(post_save, sender=VariantAttribute)
@receiver(post_save, sender=Manufacturer)
@receiver(post_save, sender=Category)
def create_preference_instance(sender, instance, created, **kwargs):

    if created:
        preference.objects.create(
            content_type=ContentType.objects.get_for_model(sender),
            object_id=instance.id,
        )


#  pointallocations
# This model must look to allocating points on a user/ ai bases for each action performed in relation to most models created
# first a model must be created for storing actions and the point allocation and also if possible its conversion to money/ monitory value
# Points should be allorted to various activities and how each point is dirrected at or against a particular future outcome
# this will be used to create a point system for the company and monitor user performance and train the ai
# class pointallocations(models.Model):
#     action=models.CharField(_("Action"), max_length=100)
#     points=models.IntegerField(_("Points"))
#     conversion_rate=models.DecimalField(_("Conversion Rate"), max_digits=10, decimal_places=2)
#     company=models.ForeignKey(
#         Company, verbose_name=_("Company"), on_delete=models.CASCADE
#     )
#     user = models.ForeignKey(
#         User,
#         verbose_name=_("User"),
#         on_delete=models.CASCADE,
#     )
#     created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
#     updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
#     class Meta:


import pandas as pd

def load_base_init_data():
    print(Company.objects.all().count()) 

    if Company.objects.all().count() == 0:
        countries=pd.read_csv('./testdummy/data/countries.csv')
        countries = countries[countries['name'] =='Ghana'] 

        for index, row in countries.drop_duplicates().iterrows():
            country,created=Country.objects.get_or_create(
                name=row["name"],
                iso3=row["iso3"],
                iso2=row["iso2"],
                numeric_code=row["numeric_code"],
                phone_code=f'+{row["phone_code"]}',
                currency=row["currency"],
                currency_name=row["currency_name"],
                lat=row["latitude"],
                lon=row["longitude"],
            )
            
        states=pd.read_csv('./testdummy/data/states.csv')
        states=states[states['country_name']=='Ghana']
        for index, row in states.drop_duplicates().iterrows():
            count=Country.objects.get(name=row["country_name"],iso2=row['country_code'])
            try:
                state,created=State.objects.get_or_create(
                    name=row["name"],
                    country=count,
                    state_code=row["state_code"],
                    lat=row["latitude"],
                    lon=row["longitude"],
                )
                
                
            except Exception as e:
                print(e)
                pass
        
        cities=pd.read_csv('./testdummy/data/cities.csv')
        cities=cities[cities['country_name']=='Ghana']
        for index, row in cities.drop_duplicates().iterrows():
            
            try:
                city,created=City.objects.get_or_create(
                    name=row["name"],
                    state=State.objects.get(name=row["state_name"],state_code=row["state_code"],country__iso2=row["country_code"]),
                    lat=row["latitude"],
                    lon=row["longitude"],
                )
            except Exception as e:
                print(e)
                pass
    else:
        print('Done')
    

```

```python

from django.db import models
import re
# Create your models here.
from django.db import models
from django.utils.translation import gettext_lazy as _
from party.models import Client, Staff
from department.models import Branch, Department
from addons.models import createdtimestamp_uid,activearchlockedMixin
from party.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from accounts.models import Charts_of_account, Account, Tax, Transaction, BankAccount,Bank
from inventory.models import (
    Item,
    ItemLot,
    unit,  
    unitofmeasure,
    item_pricing_department,
)
from django.urls import reverse
from djmoney.models.fields import MoneyField,CurrencyField
from addons.models import discount
# Create your models here.

# https://www.omg.org/retail-depository/arts-odm-73/%7B80781E5D-3EC3-4D84-A451-A73B3D5C31F2%7D+00000000.html



# Tender includes all the forms of payment that are accepted by the RETAIL STORE in settling sales and other transactions. 
# It defines the retailer's policy for handling each different tender type it accepts.




class Tender_Repository(createdtimestamp_uid,activearchlockedMixin):
    '''
    Describes the types of physical tender containers used in the retail enterprise.
    This tracks the amount of money in available at each tenderrepository accross branches 
    Tender repository generally includes assets like, store safe(s), tills, bank or other institution  etc.
    A repository within the enterprise for safekeeping of Tender removed from the Till and/or Tills. 
    This includes "Safe", "LockBox", "SecureLocation".

    lockoutamount: The amount of Cash that must be in the Till to cause the Workstation holding the Till to cease to accept new Transactions.
    lockoutwarningamount: The amount of Cash that must be in the Till to cause a warning to be displayed on screen to the Operator.
    '''

    repository=(
        ('Safe','Safe'),
        ('MobileMoney','MobileMoney'),
        ('Till','Till'),
        ('LockBox','LockBox'),
        )

    name=models.CharField(_("Tender Repo Name"), max_length=50,)
    description=models.TextField(_("Description"),null=True,blank=True)
    tender_repo_type=models.CharField(_("Tender Repository Type"), max_length=50,choices=repository,default='Safe')

    branch=models.ForeignKey(Branch, verbose_name=_("Sale Location"), on_delete=models.CASCADE,related_name='branch_tender_repositories')
    # defaultopeningcashbalance dictates how much money must be left behind during transfer... defaults to 0 when type is not till
    open_cash_drawer = models.BooleanField(_("Open Cash Drawer"), default=False) #when set to true, the cash drawer must be opened to receive the payment
    
    openingcashbalanceamount = MoneyField(max_digits=14, decimal_places=2, default_currency='GHS',default=0)
    # computerid/ipaddress is the unique identifier for the tender repository
    lockoutamount=MoneyField(max_digits=14, decimal_places=2, default_currency='GHS',default=0)
    lockoutwarningamount=MoneyField(max_digits=14, decimal_places=2, default_currency='GHS',default=0) #should idealy be between 50% and 75% of lockoutamount
    # each one of these must hold an account value for each tender repository
    account=models.ForeignKey(Account, verbose_name=_("Tender Repo Account"), 
                              on_delete=models.CASCADE,null=True,blank=True,editable=False,related_name='tender_repositories'
                              )

    class Meta:
        verbose_name = _("Tender Repository")
        verbose_name_plural = _("Tender Repositories")
        unique_together=('name','branch','tender_repo_type')


    def clean_lockamount(self):
        '''
        A rule defining an amount of Cash that is allowed to be held in a Till at any one time, and the action the POS Application is to take when the calculated amount of cash in exceeds the limit.

        '''
        # check if lockoutamount is less than or equal to lockoutwarningamount and raise validation error
        if self.lockoutamount.currency is not self.lockoutwarningamount.currency:
            raise ValidationError(
                {
                    'lockoutwarningamount':_("Currency is not the same as Lock Out Amount"),
                    'lockoutamount':_("Currency is not the same as Lock Out Warning Amount"),
                 }
                )

        if not self.lockoutamount.amount > self.lockoutwarningamount.amount:
            raise ValidationError(
                {'lockoutwarningamount':_("Lock Out Warning Amount must be less than the Lock Out Amount. Ideally should be between 0.5 and 0.75 of Lock Out Amount.")}
                )
        pass
    
    def clean_department(self):
        if self.branch.department is not self.tender.department:
            raise ValidationError(
                {
                    'tender':_("Select an Appropriate Tender... Tender and Branch Must belong to the same Sale Department"),
                 }
                )
        pass

    def clean(self):
        self.clean_department()
        # self.clean_lockamount()
        return super().clean()


    def __str__(self):
        # branchname with repo type and then repo number
        return self.name

    def get_absolute_url(self):
        return reverse("tenderrepository_detail", kwargs={"pk": self.pk})

    
    def save(self, *args, **kwargs):
          # debit Cash is to be moved to tender repositories see sales module
        
        super(Tender_Repository, self).save(*args, **kwargs) # Call the real save() method


class WorkStation(createdtimestamp_uid):
    '''
    A device used as an as interface to any store business function. 
    This includes the capture and storage of TRANSACTIONS and operational performance reporting.
    All work stations must be associated with a tenderrepository. This will allow the admin know exactly where each tender was recieved.
    Work stations are synanomous to a 
    Tenderre 
    '''
    branch=models.ForeignKey(Branch, verbose_name=_("Sale Location"), on_delete=models.CASCADE,editable=False,related_name='branch_work_stations')
    name=models.CharField(_("Name"), max_length=50, unique=True,editable=False) #a workstation name, Work Station name follows a convension of Branchname_Workstationnumber...eg Accra_01
    tender_till=models.ForeignKey(Tender_Repository, verbose_name=_("Tender Repository Till"),
                                        on_delete=models.CASCADE,
                                        limit_choices_to={'tender_repo_type':'Till'}
                                        )
                                        # limit choices to all but safe(simply cos a safe is not and can not be a work station)   
    intraining=models.BooleanField(_("In Training"),default=False) # must have a limited timer and allows for training 
    key=models.CharField(_("Key"),unique=True, max_length=50, null=True, blank=True)
    # check till opening counts between 
    #  
    allowedstaff=models.ManyToManyField(Staff, verbose_name=_("Allowed Work Station Staff"))# add a validation preventing staff not allowed from making sales on the till/work station...hence access must be cause an allert letting the staff know there are not allowed here
    # ensure that allowed staff belong to the branch department staff list
    class Meta:
        verbose_name = _("workstation")
        verbose_name_plural = _("workstations")
        unique_together = ('branch', 'tender_till',)
        permissions = [
            ("can_retrain_workstation", "Can Retrain Workstation"),
            ("can_endtraining_workstation", "Can End Training Workstation"),
            ("can_change_workstation_staff", "Can Change Workstation Allowed Staff"),
            
        ]

    def __str__(self):
        return self.name

    def clean(self):
        # ensure that each assigned staff bellongs to the branch department staff list
        print(self.allowedstaff.all())
        print(self.branch.staffbranch.all())
        # for staff in self.allowedstaff.all():
        #     if staff not in self.branch.department.staffs.all():
        #         raise ValidationError(
        #             {
        #                 'allowedstaff':_(
        #                     f"Staff {staff.user.get_full_name()} does not belong to the branch department staff list."
        #                 ),
        #              }
        #             )
                    
        return super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        self.branch=self.tender_till.branch
        if self._state.adding:  # Only generate sale number if the object is being created
            count=WorkStation.objects.filter(branch=self.branch).count()+1
            self.name = f"{self.branch.name}_{self.tender_till.name}_{count:03d}"
       
        for staff in self.allowedstaff.all():
            if staff not in self.branch.staffbranch.all():
                raise ValidationError(
                    {
                        'allowedstaff':_(
                            f"Staff {staff.user.get_full_name()} does not belong to the branch department staff list."
                        ),
                     }
                    )
        super(WorkStation, self).save(*args, **kwargs)  # Call the real save() method


    def get_absolute_url(self):
        return reverse("workstation_detail", kwargs={"pk": self.pk})


class SaleReturnReason(createdtimestamp_uid,activearchlockedMixin):

    name=models.CharField(_("Return Reason Code"), max_length=50,)
    description=models.CharField(_("Description"), max_length=225, null=True, blank=True)
    class Meta:
        verbose_name = _("Sale Return Reason")
        verbose_name_plural = _("Sale Return Reasons")

    def __str__(self):
        return self.name
    
    # auto generate code
    def save(self, *args, **kwargs):
        # if self._state.adding:  # Only generate sale number if the object is being created
        #     # generate code by taking first three letters of name and appending a count of existing codes with same first three letters
        #     prefix = re.sub(r'\W+', '', self.name[:3]).upper()
        #     count = SaleReturnReason.objects.filter(name__startswith=prefix).count() + 1
        #     # an error may occur if two reasons with same first three letters are created and deleted before saving the next one
        #     # so 
        #     self.name = f"{prefix}_{count:03d}"
        super(SaleReturnReason, self).save(*args, **kwargs)  # Call the real save() method


    def get_absolute_url(self):
        return reverse("SaleReturnReason_detail", kwargs={"pk": self.pk})


class Sale_Return(createdtimestamp_uid):
    '''
    A type of Transaction that records the business conducted between the retail enterprise and another party involving the exchange in ownership and/or accountability for merchandise and/or tender or involving the exchange of tender for services
    '''

    branch=models.ForeignKey(Branch, verbose_name=_("Branch"), on_delete=models.CASCADE, editable=False,)
    
    status=models.CharField(_("Status"), max_length=50, choices=[
        ('pending', 'pending'),
        ('approved', 'approved'),
        ('void', 'void'),
    ])
    voided_by=models.ForeignKey(Staff, verbose_name=_("Return By"), on_delete=models.CASCADE,null=True,blank=True, editable=False, related_name='sale_voided_by_staff')
    sale_number = models.CharField(_("Sale Number"), max_length=100,editable=False)
    line_number=models.PositiveIntegerField(_("Line Number"), null=True, blank=True, editable=False)
    sale_return_reason=models.ForeignKey(SaleReturnReason, verbose_name=_("Return Reason"), on_delete=models.CASCADE, null=True, blank=True)
    work_station=models.ForeignKey(WorkStation, verbose_name=_("Work Station"), on_delete=models.CASCADE,)
    # null and blank must be false
    # transact_type=models.CharField(_("Transaction Type"),choices=typetransaction, max_length=50)

    # ring_elapsed_time=models.IntegerField(_("Ring Elapsed Time(seconds)")) #The total time elapsed between commencement of the RetailTransaction and the commencement of the transaction tendering process.
    # idle_elapsed_time=models.IntegerField(_("Idle Elapsed Time(seconds)")) #The total time taken that a particular Workstation was idle between completion of the previous and commencement of the current RetailTransaction	
    # unit_count= models.PositiveIntegerField(_("Unit Count"))
    # scanned_item_count=models.PositiveIntegerField(_("Scanned Item Count"))
    # keyed_item_count=models.PositiveIntegerField(_("Keyed Item Count"))
    # receipt_date_time=models.DateTimeField(_("Receipt Date Time"), auto_now=False, auto_now_add=False)
    client=models.ForeignKey(User, verbose_name=_("Client"), on_delete=models.CASCADE, null=True,blank=True,limit_choices_to={'is_vendor': False})
    staff=models.ForeignKey(Staff, verbose_name=_("Staff"), on_delete=models.CASCADE, related_name='sale_staff', editable=False)
    tax = models.ManyToManyField(Tax, verbose_name=_("Tax"),blank=True)
    due_amount_before_tax_discount=MoneyField(
        _("Due Amount Before Tax/Discount"), max_digits=20, decimal_places=2,default=0,default_currency='GHS',
        editable=False
    )
    discount_amount=MoneyField(
        _("Discount Amount"), max_digits=20, decimal_places=2,default=0,default_currency='GHS'
    )
    cost_of_goods_sold=MoneyField(
        _("Cost of Goods Sold"), max_digits=20, decimal_places=2,default=0,default_currency='GHS',
        editable=False
    )
    total_taxable_amount=MoneyField(
        _("Taxable Amount"), max_digits=20, decimal_places=2,default=0,default_currency='GHS',
        editable=False
    )
    tax_amount_total=MoneyField(
        _("Tax Amount Total"), max_digits=20, decimal_places=2,default=0,default_currency='GHS',
        editable=False
        # calculated input showing the total taxed amount associated with the sale of goods
    )
    due_amount=MoneyField(
        _("Due Amount"), max_digits=20, decimal_places=2,default=0,default_currency='GHS'
    )

    credit_amount=MoneyField(
        _("Credit Amount"), max_digits=20, decimal_places=2,default=0,default_currency='GHS'
    )
    tip_amount=MoneyField(
        _("Tip Amount"), max_digits=20, decimal_places=2,default=0,default_currency='GHS'
    )
    amount_paid = MoneyField(
        _("Paid Amount"), max_digits=20, decimal_places=2,default_currency='GHS',
    )
    balance_amount = MoneyField(
        _("Balance Amount"), max_digits=20, decimal_places=2,default_currency='GHS',default=0,
        editable=False
    )
    
    notes = models.TextField(_("Notes"),null=True, blank=True)
    
    class Meta:
        verbose_name = _("Sale Return")
        verbose_name_plural = _("Sale Returns")
        unique_together = ('sale_number', 'branch',)
        permissions = [
            ("can_reverse_sale_return", "Can Reverse Sale Return"),
            ("can_void_sale_return", "Can Void Sale Return"),
        ]

    def clean_return_reason(self):
        if self.status=='void' and self.sale_return_reason is None:
            raise ValidationError(
                {
                    'sale_return_reason':_("Please provide the reason for the Return"),
                 }
                )
        elif self.status=='void' and self.voided_by is None:
            raise ValidationError(
                {
                    'voided_by':_("Please provide the staff that voided this sale return transaction"),
                })
        else:
            pass
    
    def clean_checkpendingmoney(self):
        #  check payment and currency and pending payment amount
        # if self.amountpaid > self.due_amount:
        # first 
        # if self.due_amount.money 
        pass

    def clean_checkClient(self):
        
        pass

    
    def clean(self):
        self.clean_return_reason()
        return super().clean()

    def __str__(self):
        return self.sale_number

    def get_absolute_url(self):
        return reverse("Sale_Return_detail", kwargs={"pk": self.pk})
    
    def save(self, *args, **kwargs):
        if self._state.adding:  # Only generate sale number if the object is being created
            count=Sale_Return.objects.filter(branch=self.branch,created_at__date=timezone.now().date()).count()+1
            # prefix with bill with inv_ and suffix with count padded to 5 digits with date at the end
            self.line_number=count
            self.sale_number = f"INV_{timezone.now().strftime('%Y%m%d')}_{count:05d}"
        self.due_amount_before_tax_discount=self.due_amount- self.discount_amount + self.tax_amount_total
        self.balance_amount= self.amount_paid - self.due_amount - self.tip_amount
        # if self.status=='void':
            # self.voided_by
        self.full_clean()
        super(Sale_Return, self).save(*args, **kwargs) # Call the real save() method


class Sale_Return_Item(createdtimestamp_uid):

    sale_return_line=models.ForeignKey(
        Sale_Return, 
        verbose_name=_("Sale Return Transaction"),
        on_delete=models.CASCADE,
        related_name='sale_return_items'
        )
    void=models.BooleanField(_("Void"),default=False)
    line_number=models.CharField(_("Line Number"), max_length=50,blank=True,null=True,editable=False)
    item = models.ForeignKey(
        Item, verbose_name=_("item"), on_delete=models.PROTECT
    )
    
    
    class Meta:
        verbose_name = _("sale_return_item")
        verbose_name_plural = _("sale_return_items")
        unique_together = ('sale_return_line', 'item',)

    def __str__(self):
        return self.line_number

    def get_absolute_url(self):
        return reverse("sale_return_item_detail", kwargs={"pk": self.pk})
    def save(self, *args, **kwargs):
        # if self._state.adding:  # Only generate sale number if the object is being created
        count=Sale_Return_Item.objects.filter(sale_return_line=self.sale_return_line).count()+1
        if self._state.adding:
            self.line_number = f"{count}"
        super(Sale_Return_Item, self).save(*args, **kwargs) # Call the real save() method



class Sale_Return_Detail(createdtimestamp_uid):
    sale_item=models.ForeignKey(Sale_Return_Item, verbose_name=_("Sale Return Item"), on_delete=models.CASCADE, related_name='sale_return_detail')
    item_lot = models.ForeignKey(
        ItemLot,
        verbose_name=_("Item Lot Details"),
        on_delete=models.PROTECT,
    )
    uom = models.ForeignKey(
        unitofmeasure,
        verbose_name=_("Unit of Measure"),
        on_delete=models.CASCADE,
        editable=False
    )
    uom_qty=models.PositiveIntegerField(
        _("UOM Quantity"), editable=False
    )
    # this is gotten from the item pricing department
    line_number=models.CharField(_("Line Number"), max_length=50,blank=True,null=True,editable=False)
    selling_price_department=models.ForeignKey(item_pricing_department, verbose_name=_("Selling Price Department"), on_delete=models.CASCADE)
    unit_sell_price = MoneyField(
        _("Selling Price per UOM"), max_digits=20, decimal_places=2,default=0,default_currency='GHS'
    )
    unit_cost_price = MoneyField(
        _("Unit Cost Price"), 
        max_digits=25, 
        decimal_places=2,
        default=0,
        default_currency='GHS',
        editable=False
    )
    unit_tax_amount = MoneyField(
        _("Unit Tax Amount"), max_digits=20, decimal_places=2,default=0,default_currency='GHS'
    )
    qty = models.PositiveIntegerField(
        _("Quantity")
    )
    qty_base= models.PositiveIntegerField(
        _("Quantity in Base UOM"), null=True, blank=True, editable=False
    )
    line_total = MoneyField(
        _("Unit Line Amount Price"),
        max_digits=25,
        decimal_places=2,default=0,default_currency='GHS',
        editable=False
    )

    class Meta:
        verbose_name = _("Sale Return Detail")
        verbose_name_plural = _("Sale Return Details")
        unique_together=('sale_item', 'item_lot','selling_price_department')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Sale_Return_Detail_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if self._state.adding:  # Only generate sale number if the object is being created
            count=Sale_Return_Detail.objects.filter(sale_item=self.sale_item).count()+1
            self.line_number = f"{count}"
        self.uom=self.selling_price_department.uom
        self.uom_qty=self.uom.conversion_rate
        # self.unit_sell_price=self.selling_price_department.selling_price
        self.line_total=self.unit_sell_price * self.qty
        self.qty_base=self.qty * self.uom_qty
        super(Sale_Return_Detail, self).save(*args, **kwargs) # Call the real save() method


class cashpayment(createdtimestamp_uid):
    sale_return = models.ForeignKey(Sale_Return, verbose_name=_("Sale Return"), on_delete=models.PROTECT,
        related_name='cash_payments'
    )
    amount = MoneyField(
        _("Amount"), max_digits=20, decimal_places=2, default=0, default_currency='GHS'
    )
    repository = models.ForeignKey(Tender_Repository, verbose_name=_("Tender Repo"), on_delete=models.PROTECT,
        related_name='cash_payments_repo',
        limit_choices_to={'tender_repo_type':'Till'}
    )
    

    # payment_method=models.CharField(_("Payment Type"), max_length=50, choices=paymethods)
    class Meta:
        verbose_name = _("cashpayment")
        verbose_name_plural = _("cashpayments")
        unique_together = ('sale_return', 'repository',)

    def __str__(self):
        return str(self.amount)

    def get_absolute_url(self):
        return reverse("cashpayment_detail", kwargs={"pk": self.pk})

# Cash
class momopayment(createdtimestamp_uid):
    phone_number = models.CharField(_("Phone Number"), max_length=50)
    networkchoices = (
        ('MTN', 'MTN'),
        ('VODAFONE', 'VODAFONE'),
        ('AIRTELTIGO', 'AIRTELTIGO'),
    )
    network = models.CharField(_("Network"), max_length=50, choices=networkchoices)
    repository = models.ForeignKey(Tender_Repository, verbose_name=_("Tender Repo"), on_delete=models.PROTECT,
        related_name='momo_payments_repo',
        limit_choices_to={'tender_repo_type':'MobileMoney'}
    )
    sale_return = models.ForeignKey(Sale_Return, verbose_name=_("Sale Return"), on_delete=models.PROTECT,
        related_name='momo_payments'
    )
    amount=MoneyField(
        _("Amount"), max_digits=20, decimal_places=2,default=0,default_currency='GHS'
    )
    # payment_method=models.CharField(_("Payment Type"), max_length=50, choices=paymethods)
    class Meta:
        verbose_name = _("momopayment")
        verbose_name_plural = _("momopayments")
        unique_together = ('sale_return', 'repository',)

    def __str__(self):
        return str(self.amount)

    def get_absolute_url(self):
        return reverse("momopayment_detail", kwargs={"pk": self.pk})

class creditpayment(createdtimestamp_uid):
    sale_return=models.ForeignKey(Sale_Return,verbose_name=_("Sale Return"), on_delete=models.PROTECT,
        related_name='credit_payments'
    )
    client = models.ForeignKey(Client, verbose_name=_("Client"), on_delete=models.PROTECT,)
    amount = MoneyField(
        _("Amount"), max_digits=20, decimal_places=2, default=0, default_currency='GHS'
    )
    class Meta:
        verbose_name = _("creditpayment")
        verbose_name_plural = _("creditpayments")
        unique_together = ('sale_return', 'client',)

    def __str__(self):
        return str(self.amount)

    def get_absolute_url(self):
        return reverse("creditpayment_detail", kwargs={"pk": self.pk})


# for weather condition checks
# https://open-meteo.com/en/docs?current=precipitation,rain,showers,snowfall,is_day,apparent_temperature,wind_speed_10m&latitude=4.8875&longitude=-1.7608


###custoner orders
class ClientOrder(createdtimestamp_uid, models.Model):
    ##add a way for a specific department to handle a specific Client grouping
    # Client orders can be null indicating Client orders that are done by anonymous Clients
    paymentstaus = (("paid", "paid"), ("unpaid", "unpaid"))
    # ordertype = models.CharField(_("Sales Order Type"), max_length=50, choices=salder)
    orderpaymentstatus = models.CharField(
        _("Payment Status"), choices=paymentstaus, max_length=50
    )
    orderdate = models.DateField(_("order date"), auto_now=False, auto_now_add=False)
    expectedfullfilmentdate = models.DateField(
        _("Expected fulfilment date"), auto_now=False, auto_now_add=False
    )
    Client = models.ForeignKey(
        Client, verbose_name=_("Client"), on_delete=models.CASCADE
    )
    dueamount = MoneyField(_("Amount"), max_digits=25, decimal_places=2,
        default=0,default_currency='GHS'
    )
    
    class Meta:
        verbose_name = _("ClientOrder")
        verbose_name_plural = _("ClientOrders")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("ClientOrder_detail", kwargs={"pk": self.pk})


class RecurrentCustOrder(createdtimestamp_uid, models.Model):
    # Autorefil
    # frequency
    # begin
    # last supppleied date.
    # next supply date
    # price charged
    # paid for in advance
    # picture orders...processed status and fulfilled
    #


    # create another table that holds Clients with order details and
    # 
    class Meta:
        verbose_name = _("RecurrentCustOrder")
        verbose_name_plural = _("RecurrentCustOrders")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("RecurrentCustOrder_detail", kwargs={"pk": self.pk})


class ClientOrderLineitem(createdtimestamp_uid, models.Model):
    item = models.ForeignKey(Item, verbose_name=_("item"), on_delete=models.CASCADE)
    description = models.CharField(_("Description"), max_length=50)
    ClientOrder = models.ForeignKey(
        ClientOrder,
        verbose_name=_("Client Order"),
        on_delete=models.CASCADE,
        related_name="Clientoder",
    )
    fulfilled = models.BooleanField(_("Fulfiled"), default=False)
    OrderedItemQuantity = models.PositiveIntegerField(_("Order Item Quantity"))
    FulfilledItemQuantity = models.PositiveIntegerField(_("Fulfilled Item Quantity"))
    productsellingprice = models.ForeignKey(
        item_pricing_department,
        verbose_name=_("Seling Price"),
        on_delete=models.CASCADE,
    )
    SaleUnitRetailPriceAmount = models.DecimalField(
        _("Sale Unit Retail Price Amount"), max_digits=5, decimal_places=2
    )
    EstimatedAvailabilityDate = models.DateTimeField(
        _("Estimated Availability Date"), auto_now=False, auto_now_add=False
    )
    ActualAvailabilityDate = models.DateTimeField(
        _("Actual Availability Date"), auto_now=False, auto_now_add=False
    )

    class Meta:
        verbose_name = _("ClientOrderLineitem")
        verbose_name_plural = _("ClientOrderLineitems")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("ClientOrderLineitem_detail", kwargs={"pk": self.pk})

```


```python

from django.db import models

# Create your models here.

# this module will define settings related models such as AppConfig, UserPreferences, SystemSettings, etc.
# these models will help in managing application configurations and user preferences within the ERP system.
# further implementation will include fields, methods, and relationships relevant to settings management.
# this is a placeholder for future development.

class AppConfig(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.key}: {self.value}"
class UserPreferences(models.Model):
    user_id = models.IntegerField()
    preference_key = models.CharField(max_length=255)
    preference_value = models.TextField()

    def __str__(self):
        return f"User {self.user_id} - {self.preference_key}: {self.preference_value}"

```


```python

from django.db import models
from addons.models import createdtimestamp_uid,activearchlockedMixin
from django.urls import reverse
from party.models import Staff, Occupation,User

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
# from party.models import Staff, User
# from django.contrib.postgres.fields import HStoreField, ArrayField
from django.utils.translation import gettext_lazy as _

# Create your models here.


# action workflow management system

# config has the following fields
# name:the name of the field
# description
# required: boolean
# field_type: text, number, date, boolean, select,object, array/list
# the config field is a json field that stores the configuration of the action node
# creating a config model defines what fields are required for each action type
class configuration(createdtimestamp_uid):
    staff=models.ForeignKey(Staff,on_delete=models.SET_NULL,null=True,related_name='configuration_created_by')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    max_size=models.IntegerField(blank=True,null=True)
    required = models.BooleanField(default=False)
    field_type = models.CharField(max_length=50, choices=(
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        
        ('boolean', 'Boolean'),
        ('select', 'Select'),
        ('object', 'Object'),
        ('array', 'Array/List'),
        ('file', 'File'),
    ))
    # write the parser function for each parsertype
    def parser_function(self,value):
        if self.field_type=='text':
            return str(value)
        elif self.field_type=='number':
            return float(value)
        elif self.field_type=='date':
            from dateutil import parser
            return parser.parse(value)
        elif self.field_type=='boolean':
            if str(value).lower() in ['true','1','yes','y']:
                return True
            elif str(value).lower() in ['false','0','no','n']:
                return False
            else:
                raise ValueError("Invalid boolean value")
        elif self.field_type=='select':
            if self.options and value in self.options:
                return value
            else:
                raise ValueError("Invalid select option")
        elif self.field_type=='object':
            import json
            if isinstance(value,str):
                # parse the json string
                return json.loads(value)
            elif isinstance(value,dict):
                return value
            else:
                raise ValueError("Invalid object value")
        elif self.field_type=='array':
            import json
            if isinstance(value,str):
                return json.loads(value)
            elif isinstance(value,list):
                return value
            else:
                raise ValueError("Invalid array value")
        else:
            raise ValueError("Unknown field type")

    parserlist = [
        ('text',(
            ('text_parser', 'Text Parser'),
            ('email_parser', 'Email Parser'),
            ('url_parser', 'URL Parser'),

        )),
        ('number',(
            ('number_parser', 'Number Parser'),
            ('decimal_parser', 'Decimal Parser'),
            # what is the difference between float and decimal parser
            # A decimal parser ensures precision and is used for financial calculations
            # a float parser is used for general numerical values where precision is not critical
            ('float_parser', 'Float Parser'),
            ('integer_parser', 'Integer Parser'),
            ('positive_integer_parser', 'Positive Integer Parser'),
            ('negative_integer_parser', 'Negative Integer Parser'),
            # currency parser is a combination of amount and a currency code
        )),
        ('date',(
            ('date_parser', 'Date Parser'),
            ('datetime_parser', 'Datetime Parser'),
            ('time_parser', 'Time Parser'),
        )),
        ('boolean',(
            # ensures the value is either true or false or 1 or 0 or 'true' or 'false' or truthy or falsy

            ('boolean_parser', 'Boolean Parser'),
        )),
        ('select',(
            ('select_parser', 'Select Parser'),
            # select parser allows selection from predefined options and ensures the value is one of the options
        )),
        ('object',(
            ('object_parser', 'Object Parser'),
            # the object parser is a nested parser that allows defining sub-fields within the object
            # the object parser looks at the subfields and ensures each subfield is parsed according to its predefined parser

            # object parser ensures the value is a valid JSON object
        )),
        ('array',(
            # ('array_of_text_parser', 'Array of Text Parser'),
            # array of text parser ensures the value is an array of strings,
            # ('array_of_number_parser', 'Array of Number Parser'),
            ('array_parser', 'Array of Objects Parser'),
            # ensures the value is an array of objects and each object is parsed according to the array_item_type's parser
            # array of 
            # array parsers ensure the value is an array of the specified type
        )),
        ('file',(
            ('xlsx', 'Excel File Parser'),
            ('csv', 'CSV File Parser'),
            ('pdf', 'PDF File Parser'),
            ('image', 'Image File Parser'),
            ('docx', 'Document File Parser'),
            # file parser ensures the value is a valid file upload
        )),
    ]
    #  choices=[(item[0], item[1]) for group in parserlist for item in group[1]]
    parser= models.CharField(max_length=50,choices=parserlist, blank=True, null=True)
    # a parser defines the function name to be called when the value of the field is to be parsed
    # parsers include number_parser, date_parser, boolean_parser, text_parser, email_parser, json_parser, array_of_text_parser, array_of_number_parser,url_parser,custom_parser
    # parsers are grouped by field type
    # if field_type is number, then parser can be number_parser, decimal_parser,float_parser, integer_parser
    # if field_type is date, then parser can be date_parser, datetime_parser, time_parser,
    # if field_type is boolean, then parser can be boolean_parser
    # if field_type is text, then parser can be text_parser, email_parser, url_parser, 
    # if select, then parser can be select_parser, 
    # parser=
    # if field_type is select, then options fieldlist is required, that is Array(strings)
    options = models.JSONField(blank=True, null=True)
    # if field_type is object, then sub_fields is required, that is a ManyToManyField to self,
    sub_fields = models.ManyToManyField('self',blank=True)
    # if field_type is array, then array_item_type is required, that is a ForeignKey to self, and should always be mapped to an object type
    array_item_type = models.ForeignKey('self',blank=True, null=True, on_delete=models.CASCADE, related_name='array_item_types',limit_choices_to={'field_type': 'object'})
    # default parameters hold default values for the configuration field and should be provided in  
    

    def clean(self):
        # validate that options is provided if field_type is select
        if self.field_type == 'select' and not self.options:
            raise ValueError("Options field is required for select field type")
        # validate that sub_fields is provided if field_type is object
        if self.field_type == 'object' and not self.sub_fields.exists():
            raise ValueError("Sub-fields are required for object field type")
        # validate that array_item_type is provided if field_type is array
        if self.field_type == 'array' and not self.array_item_type:
            raise ValueError("Array item type is required for array field type")
        # validate that array_item_type is of field_type object
        if self.field_type == 'array' and self.array_item_type and self.array_item_type.field_type != 'object':
            raise ValueError("Array item type must be of field type object")


        # ensure that the parser is valid for the field type
        valid_parsers = [item[0] for group in self.parserlist if group[0] == self.field_type for item in group[1]]
        if self.parser and self.parser not in valid_parsers:
            raise ValueError(f"Invalid parser '{self.parser}' for field type '{self.field_type}'")
        super().clean()
    
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse("configuration_detail", kwargs={"pk": self.pk})
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

# activity nodes
# 

class node(createdtimestamp_uid,activearchlockedMixin):
    staff=models.ForeignKey(Staff,on_delete=models.SET_NULL,null=True,related_name='node_created_by')
    
    # cronjobtriggers events are either time-based or event-based triggers that initiate the execution of cron jobs.
    # event-based triggers are either system events or user-defined events that cause a cron job to run when specific conditions are met.

    # schedule format:
    # ┌───────────── minute (0 - 59)
    # │ ┌───────────── hour (0 - 23)
    # │ │ ┌───────────── day of month (1 - 31)
    # │ │ │ ┌───────────── month (1 - 12)
    # │ │ │ │ ┌───────────── day of week (0 - 6, where 0 = Sunday)
    # │ │ │ │ │
    # * * * * * 
    # 
    # Minute: {minute} (0-59)
    # Hour: {hour} (0-23)
    # Day of Month: {day} (1-31)
    # Month: {month} (1-12)
    # Day of Week: {weekday} (0-6, where 0 = Sunday)

    

    # cron jobs are scheduled tasks that run at specific intervals to perform automated actions within the system.

    node_type_choices = (
        # trigger, action, add, human activity
        # trigger has 3 types: time-based, event-based, manual
        ('trigger', (
            # time-based triggers lead to the creation of a cron job that triggers the action at specified times
            ('time_based', 'Time Based'), # time-based triggers are scheduled to run at specific times or intervals using cron expressions or predefined schedules
            ('event_based', 'Event Based'), # event-based triggers are triggered by external events such as webhooks, database changes, file uploads, etc.
            ('manual', 'Manual'), # manual triggers have an input parameter of just boolean and returns true if called
        )),
        ('action', (
            ('parse_data', 'Parse Data'), # this action node parses input data using predefined parsers and returns the parsed output. So it takes input parameters such as data_to_parse:object, parser_type:text, etc.
            ('send_email', 'Send Email'), # this action sends an email to the specified recipient(s), and can include takes as input parameters such as to_email, from_email:text, subject, body, attachments, cc, bcc, etc.
            ('http_request', 'HTTP Request'), # this action makes an HTTP request to a specified URL with given method, headers, and body, and returns the response. It takes input parameters such as url, method, headers, body, etc.
            ('database_query', 'Database Query'), # this action performs a database query such as select, insert, update, delete on a specified database table and returns the query result. It takes input parameters such as query_type, table_name, query_conditions, update_values, insert_values, etc.
            # in_practice the database_query sends either a get/post/put/delete request to a server url, given the right permissions,ofcos if the user does not have the right permissions then that access is not provided, and with 
            ('ai_model_call', 'AI Model Call'), # this action calls an AI model API with given input data and returns the model's output. It takes input parameters such as model_name, input_data, api_key, etc.
            ('notify_user', 'Notify User'), # this action sends a notification to a specified user via email, SMS, or in-app notification. It takes input parameters such as user_id, notification_type, message, etc.
            ('condition_check', 'Condition Check'), # this action evaluates specified conditions on input data and returns true or false. It takes input parameters such as conditions:object, input_data:object, etc.
        #    best use of a condition check is to use it as a trigger for an event-based trigger node
            # ('data_transformation', 'Data Transformation'), # this action transforms input data using predefined transformation rules and returns the transformed output. It takes input parameters such as input_data:object, transformation_rules:object, etc.

        )),
        ('human_activity', 'Human Activity'),# human activity node allows human interaction and primarily takes in an input and provides the input as the output
        ('add', 'Add'), # trigger nodes are the entry point of any action
    )
    
    version=models.CharField(_("Version"), max_length=50,default='1.0')
    name = models.CharField(max_length=255,)
    description = models.TextField(blank=True, null=True)
    x_position=models.IntegerField(default=0)
    y_position=models.IntegerField(default=0)
    # assigned_to=models.ForeignKey(Staff,on_delete=models.SET_NULL,null=True,related_name='node_assigned_to')
    assigned_to=models.ManyToManyField(Staff,blank=True,related_name='node_assigned_staff')
    node_type=models.CharField(max_length=50, choices=node_type_choices)
    input_conf=models.ManyToManyField(configuration,blank=True,related_name='node_input_configurations')
    output_conf=models.ManyToManyField(configuration,blank=True,related_name='node_output_configurations')
    class Meta:
        verbose_name = _("node")
        verbose_name_plural = _("nodes")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("node_detail", kwargs={"pk": self.pk})
    
    # if node_type is human_activity, then input_conf and output_conf must have at least one configuration each and assigned_to must be set
    def clean(self):
        if self.node_type == 'human_activity':
            # print(self.input_conf.count())
            print(self.input_conf.all())

            if not self.input_conf.exists():
                raise ValueError("Input configuration is required for human activity nodes")
            if not self.output_conf.exists():
                raise ValueError("Output configuration is required for human activity nodes")
            if not self.assigned_to:
                raise ValueError("Assigned to staff is required for human activity nodes")
        if self.node_type.startswith('trigger'):
            if not self.input_conf.exists():
                raise ValueError("Input configuration is required for trigger nodes")
            if not self.output_conf.exists():
                raise ValueError("Output configuration is required for trigger nodes")

        super().clean()
    def save(self, *args, **kwargs):
        # ensure that input_conf and output_conf are valid based on node_type
        # further validation can be added here
        self.clean()
        super().save(*args, **kwargs)




class Workflow(activearchlockedMixin,createdtimestamp_uid):
    
    staff=models.ForeignKey(Staff,on_delete=models.SET_NULL,null=True,blank=True,related_name='workflow_created_by')
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    start_date=models.DateTimeField(blank=True,null=True)
    end_date=models.DateTimeField(blank=True,null=True)
    trigger_node=models.ForeignKey(node,on_delete=models.SET_NULL,null=True,blank=True,related_name='workflow_trigger_node',limit_choices_to={'node_type__startswith': 'trigger'})
    nodes=models.ManyToManyField(node,blank=True,related_name='workflow_nodes')
    # nodes are the various action nodes that make up the workflow
    
    class Meta:
        verbose_name = _("Workflow")
        verbose_name_plural = _("Workflows")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("workflow_detail", kwargs={"pk": self.pk})

class WorkflowTransition(createdtimestamp_uid):
    workflow=models.ForeignKey(Workflow,on_delete=models.CASCADE,related_name='workflow_transitions')
    from_node=models.ForeignKey(node,on_delete=models.CASCADE,related_name='transition_from_node')
    to_node=models.ForeignKey(node,on_delete=models.CASCADE,related_name='transition_to_node')
    onError_choices = [
        ("retry", _("Retry")),
        ("fail", _("Fail")),
        ("skip", _("Skip")),
        ('restart', _('Restart')),
        # call a new node
        ("call_node", _("Call Node")),
    ]
    from_node_default=models.JSONField(blank=True,null=True,help_text=_("Default output data from the from_node to be used as input for the to_node"),default=dict)
    to_node_default=models.JSONField(blank=True,null=True,help_text=_("Default input data for the to_node"),default=dict)
    action_on_error = models.CharField(max_length=20, choices=onError_choices, default="fail", help_text=_("Action to take if an error occurs during node execution"))
    action_on_timeout_timeout = models.IntegerField(default=60, help_text=_("Timeout in minutes for node execution"))
    action_on_timeout_choices = [
        ("retry", _("Retry")),
        ("fail", _("Fail")),
        ("skip", _("Skip")),
        ('restart', _('Restart')),
        ("call_node", _("Call Node")),
    ]
    action_on_timeout = models.CharField(max_length=20, choices=action_on_timeout_choices, default="fail", help_text=_("Action to take if node execution times out"))
    timeout_action_count=models.IntegerField(default=0,help_text=_("Number of times to retry the node execution on timeout"))
    onError_node = models.ForeignKey(node, on_delete=models.CASCADE, blank=True, null=True, related_name='onerror_node', help_text=_("Node to call if action_on_error is 'call_node'"))
    error_retry_count=models.IntegerField(default=0,help_text=_("Number of times to retry the node execution on error"))
    error_retry_interval=models.IntegerField(default=5,help_text=_("Interval in seconds between retries on error"))
    error_threshold=models.IntegerField(default=5,help_text=_("Maximum number of errors allowed before taking action"))
    error_node_default=models.JSONField(blank=True,null=True,help_text=_("Default input data for the onError_node"),default=dict)
    staff= models.ForeignKey(Staff,on_delete=models.SET_NULL,null=True,related_name='workflowtransition_created_by')
    review_required = models.BooleanField(default=True)
    review_deadline = models.DateTimeField(blank=True, null=True)


    class Meta:
        verbose_name = _("Workflow Transition")
        verbose_name_plural = _("Workflow Transitions")

    def save(self, *args, **kwargs):
        # ensure that from_node and to_node belong to the same workflow
        if self.from_node not in self.workflow.nodes.all():
            raise ValueError("From node must belong to the same workflow")
        if self.to_node not in self.workflow.nodes.all():
            raise ValueError("To node must belong to the same workflow")
        if self.action_on_error == 'call_node' and not self.onError_node:
            raise ValueError("onError_node must be specified if action_on_error is 'call_node'")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.workflow.name}: {self.from_node.name} -> {self.to_node.name}"
    def get_absolute_url(self):
        return reverse("workflowtransition_detail", kwargs={"pk": self.pk})



class Assigned_Task(createdtimestamp_uid):
    # content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    # object_id = models.UUIDField()
    # source_object = GenericForeignKey("content_type", "object_id")
    workflowtransition = models.ForeignKey(WorkflowTransition, on_delete=models.CASCADE, related_name="assigned_tasks")
    exc_node = models.ForeignKey(node, on_delete=models.CASCADE, limit_choices_to={'node_type': 'human_activity'},related_name="assigned_exec_node") # this node is the node that created the assigned task and is primarily a human activity node 
    assigned_to = models.ForeignKey(Staff, related_name="assigned_tasks", on_delete=models.CASCADE)
    # status = models.CharField(max_length=50, choices=(
    #     ('pending', 'Pending'),
    #     ('in_progress', 'In Progress'),
    #     ('failed', 'Failed'),
    #     ('cancelled', 'Cancelled'),
    #     ('completed', 'Completed'),
    #     ('archived', 'Archived'),
    # ), default='pending')
    deadline_response=models.IntegerField(blank=True,null=True,help_text=_("Deadline to respond in hours"))


    # due_date = models.DateTimeField(blank=True, null=True)
    priority = models.CharField(max_length=50, choices=(
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ), default='medium')
    reviewers = models.ManyToManyField(Staff, related_name="task_reviewers", blank=True)
    
    def save(self, *args, **kwargs):
        # ensure that if review_required is True, then reviewers must be set
        if self.review_required and not self.reviewers.exists():
            raise ValueError("Reviewers must be set if review is required")
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name = _("Assigned Task")
        verbose_name_plural = _("Assigned Tasks")

    def __str__(self):
        return f"Task: {self.task.name}({self.priority}) assigned to {self.assigned_to.user.get_full_name()}"

    def get_absolute_url(self):
        return reverse("Assigned_Task_detail", kwargs={"pk": self.pk})
    


class WorkflowExecution(createdtimestamp_uid):
    
    content_type = models.ForeignKey(ContentType, on_delete=models.DO_NOTHING)
    object_id = models.UUIDField()
    source_object = GenericForeignKey("content_type", "object_id")
    workflow=models.ForeignKey(Workflow,on_delete=models.CASCADE,related_name='workflow_executions')
    transition=models.ForeignKey(WorkflowTransition,on_delete=models.CASCADE,related_name='workflow_execution_transition')
    execution_node=models.ForeignKey(node,on_delete=models.CASCADE,related_name='workflow_execution_node')
    status=models.CharField(max_length=50, choices=(
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'), # retry logic can be implemented here
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ), default='pending')
    input_data=models.JSONField(blank=True,null=True,help_text=_("Input data for the node execution"))
    output_data=models.JSONField(blank=True,null=True,help_text=_("Output data for the node execution"))
    error_count= models.IntegerField(default=0)
    errored_at=models.DateTimeField(blank=True,null=True)
    started_at=models.DateTimeField(blank=True,null=True)
    completed_at=models.DateTimeField(blank=True,null=True)
    assigned_to=models.ForeignKey(Staff,blank=True,null=True,on_delete=models.CASCADE,related_name='workflowexecution_assigned_to')


    class Meta:
        verbose_name = _("Workflow Execution")
        verbose_name_plural = _("Workflow Executions")

    def __str__(self):
        return f"Execution of {self.workflow.name} - {self.status}"

    def get_absolute_url(self):
        return reverse("workflowexecution_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        # update started_at and completed_at based on status 
        # additional logic can be added here to handle state transitions
        super().save(*args, **kwargs)



class Review(createdtimestamp_uid):
    workflow_execution=models.ForeignKey(WorkflowExecution,on_delete=models.CASCADE,related_name='reviews')
    reviewer = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="reviews")
    rating = models.IntegerField()
    remarks = models.TextField(blank=True, null=True)
    reviewed_at=models.DateTimeField(blank=True,null=True)
    review_status=models.CharField(max_length=50, choices=(
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ), default='pending')
    review_score=models.IntegerField(blank=True,null=True)
    

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")

    def __str__(self):
        return f"Review by {self.reviewer.staff.user.get_full_name()} for Task: {self.workflow_execution.task.task.name}({self.workflow_execution.workflow.name})"

    def get_absolute_url(self):
        return reverse("Review_detail", kwargs={"pk": self.pk})

```
"""
Extended billing client with project billing and deposit management.

This module provides high-level methods for:
- Security deposit calculation and collection
- Project billing status
- Balance and transaction history
"""

import typing
from .client import BillingClient, AsyncBillingClient
from ..core.request_options import RequestOptions
from ..core.unchecked_base_model import construct_type
from ..core.api_error import ApiError
from json.decoder import JSONDecodeError
from decimal import Decimal


class DepositCalculation(typing.TypedDict):
    """Result of deposit calculation"""
    deposit_amount: float
    breakdown: typing.Dict[str, float]
    estimated_annotation_cost: float
    estimated_storage_cost: float
    minimum_deposit: float


class ProjectBillingStatus(typing.TypedDict):
    """Project billing status response"""
    project_id: int
    has_billing: bool
    state: str
    security_deposit: typing.Dict[str, float]
    costs: typing.Dict[str, float]
    storage: typing.Dict[str, typing.Any]
    activity: typing.Dict[str, typing.Any]
    lifecycle: typing.Dict[str, typing.Any]


class BillingDashboard(typing.TypedDict):
    """Billing dashboard response"""
    billing: typing.Dict[str, typing.Any]
    recent_transactions: typing.List[typing.Dict[str, typing.Any]]
    recent_payments: typing.List[typing.Dict[str, typing.Any]]


class BillingClientExt(BillingClient):
    """
    Extended billing client with project deposit and billing operations.
    
    Example:
        >>> from synapse_sdk import Synapse
        >>> client = Synapse(api_key="your-api-key")
        >>> 
        >>> # Calculate deposit for a project
        >>> deposit = client.billing.calculate_deposit(
        ...     project_id=123,
        ...     estimated_tasks=1000
        ... )
        >>> print(f"Deposit required: {deposit['deposit_amount']} credits")
        >>>
        >>> # Pay the deposit
        >>> result = client.billing.pay_deposit(project_id=123)
        >>> print(f"Deposit collected: {result['deposit_collected']}")
        >>>
        >>> # Check project billing status
        >>> status = client.billing.get_project_status(project_id=123)
        >>> print(f"Project state: {status['state']}")
    """

    def calculate_deposit(
        self,
        *,
        project_id: typing.Optional[int] = None,
        label_config: typing.Optional[str] = None,
        estimated_tasks: typing.Optional[int] = None,
        estimated_storage_gb: typing.Optional[float] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> DepositCalculation:
        """
        Calculate the security deposit required for a project.
        
        Parameters
        ----------
        project_id : int, optional
            ID of existing project to calculate deposit for
        label_config : str, optional
            XML label configuration for new projects
        estimated_tasks : int, optional
            Estimated number of tasks/files
        estimated_storage_gb : float, optional
            Estimated storage in GB
        request_options : RequestOptions, optional
            Request-specific configuration
            
        Returns
        -------
        DepositCalculation
            Deposit amount and breakdown
            
        Examples
        --------
        >>> # For existing project
        >>> deposit = client.billing.calculate_deposit(project_id=123)
        >>> 
        >>> # For new project with estimates
        >>> deposit = client.billing.calculate_deposit(
        ...     estimated_tasks=1000,
        ...     estimated_storage_gb=5.0
        ... )
        """
        body = {}
        if project_id is not None:
            body["project_id"] = project_id
        if label_config is not None:
            body["label_config"] = label_config
        if estimated_tasks is not None:
            body["estimated_tasks"] = estimated_tasks
        if estimated_storage_gb is not None:
            body["estimated_storage_gb"] = estimated_storage_gb

        _response = self._client_wrapper.httpx_client.request(
            "api/project-billing/calculate_deposit/",
            method="POST",
            json=body,
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(DepositCalculation, _response.json())
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def pay_deposit(
        self,
        *,
        project_id: int,
        deposit_amount: typing.Optional[float] = None,
        estimated_tasks: typing.Optional[int] = None,
        estimated_storage_gb: typing.Optional[float] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Dict[str, typing.Any]:
        """
        Collect security deposit for a project from organization credits.
        
        Parameters
        ----------
        project_id : int
            ID of the project to collect deposit for
        deposit_amount : float, optional
            Pre-calculated deposit amount (from calculate_deposit)
        estimated_tasks : int, optional
            Task count for deposit calculation
        estimated_storage_gb : float, optional
            Storage estimate for deposit calculation
        request_options : RequestOptions, optional
            Request-specific configuration
            
        Returns
        -------
        dict
            Result with deposit_collected, state, and project_id
            
        Raises
        ------
        ApiError
            If insufficient credits (402) or other error
            
        Examples
        --------
        >>> # Calculate and pay deposit
        >>> deposit = client.billing.calculate_deposit(project_id=123)
        >>> result = client.billing.pay_deposit(
        ...     project_id=123,
        ...     deposit_amount=deposit['deposit_amount']
        ... )
        >>> print(f"Collected: {result['deposit_collected']} credits")
        """
        body = {"project_id": project_id}
        if deposit_amount is not None:
            body["deposit_amount"] = deposit_amount
        if estimated_tasks is not None:
            body["estimated_tasks"] = estimated_tasks
        if estimated_storage_gb is not None:
            body["estimated_storage_gb"] = estimated_storage_gb

        _response = self._client_wrapper.httpx_client.request(
            "api/project-billing/collect_deposit/",
            method="POST",
            json=body,
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return _response.json()
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def refund_deposit(
        self,
        *,
        project_id: int,
        reason: typing.Optional[str] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Dict[str, typing.Any]:
        """
        Request refund of security deposit for a completed project.
        
        Parameters
        ----------
        project_id : int
            ID of the project to refund deposit for
        reason : str, optional
            Reason for refund (e.g., "Project completed")
        request_options : RequestOptions, optional
            Request-specific configuration
            
        Returns
        -------
        dict
            Refund result with amount refunded
            
        Examples
        --------
        >>> result = client.billing.refund_deposit(
        ...     project_id=123,
        ...     reason="Project completed successfully"
        ... )
        """
        body = {"project_id": project_id}
        if reason is not None:
            body["reason"] = reason

        _response = self._client_wrapper.httpx_client.request(
            "api/project-billing/refund_deposit/",
            method="POST",
            json=body,
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return _response.json()
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def get_project_status(
        self,
        *,
        project_id: int,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> ProjectBillingStatus:
        """
        Get detailed billing status for a project.
        
        Parameters
        ----------
        project_id : int
            ID of the project
        request_options : RequestOptions, optional
            Request-specific configuration
            
        Returns
        -------
        ProjectBillingStatus
            Project billing details including deposit, costs, lifecycle state
            
        Examples
        --------
        >>> status = client.billing.get_project_status(project_id=123)
        >>> print(f"Deposit paid: {status['security_deposit']['paid']}")
        >>> print(f"Credits consumed: {status['costs']['credits_consumed']}")
        """
        _response = self._client_wrapper.httpx_client.request(
            "api/project-billing/project_status/",
            method="GET",
            params={"project_id": project_id},
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(ProjectBillingStatus, _response.json())
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def get_dashboard(
        self,
        *,
        organization: typing.Optional[int] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> BillingDashboard:
        """
        Get billing dashboard with balance, transactions, and payments.
        
        Parameters
        ----------
        organization : int, optional
            Organization ID (defaults to user's active org)
        request_options : RequestOptions, optional
            Request-specific configuration
            
        Returns
        -------
        BillingDashboard
            Dashboard with billing info, transactions, payments
            
        Examples
        --------
        >>> dashboard = client.billing.get_dashboard()
        >>> print(f"Credit balance: {dashboard['billing']['credit_balance']}")
        """
        params = {}
        if organization is not None:
            params["organization"] = organization

        _response = self._client_wrapper.httpx_client.request(
            "api/billing/dashboard/",
            method="GET",
            params=params if params else None,
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(BillingDashboard, _response.json())
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def get_transactions(
        self,
        *,
        organization: typing.Optional[int] = None,
        transaction_type: typing.Optional[str] = None,
        category: typing.Optional[str] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Get credit transaction history.
        
        Parameters
        ----------
        organization : int, optional
            Organization ID
        transaction_type : str, optional
            Filter by type (credit, debit)
        category : str, optional
            Filter by category (annotation, storage, deposit, etc.)
        request_options : RequestOptions, optional
            Request-specific configuration
            
        Returns
        -------
        list
            List of credit transactions
            
        Examples
        --------
        >>> transactions = client.billing.get_transactions(category="annotation")
        >>> for txn in transactions:
        ...     print(f"{txn['description']}: {txn['amount']}")
        """
        params = {}
        if organization is not None:
            params["organization"] = organization
        if transaction_type is not None:
            params["type"] = transaction_type
        if category is not None:
            params["category"] = category

        _response = self._client_wrapper.httpx_client.request(
            "api/billing/transactions/",
            method="GET",
            params=params if params else None,
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return _response.json()
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    def get_balance(
        self,
        *,
        organization: typing.Optional[int] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Dict[str, typing.Any]:
        """
        Get current credit balance for the organization.
        
        This is a convenience method that fetches the dashboard and extracts
        the billing balance information.
        
        Parameters
        ----------
        organization : int, optional
            Organization ID
        request_options : RequestOptions, optional
            Request-specific configuration
            
        Returns
        -------
        dict
            Balance information with credit_balance and other details
            
        Examples
        --------
        >>> balance = client.billing.get_balance()
        >>> print(f"Available credits: {balance['credit_balance']}")
        """
        dashboard = self.get_dashboard(
            organization=organization,
            request_options=request_options
        )
        return dashboard.get("billing", {})


class AsyncBillingClientExt(AsyncBillingClient):
    """
    Async extended billing client with project deposit and billing operations.
    """

    async def calculate_deposit(
        self,
        *,
        project_id: typing.Optional[int] = None,
        label_config: typing.Optional[str] = None,
        estimated_tasks: typing.Optional[int] = None,
        estimated_storage_gb: typing.Optional[float] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> DepositCalculation:
        """Calculate the security deposit required for a project."""
        body = {}
        if project_id is not None:
            body["project_id"] = project_id
        if label_config is not None:
            body["label_config"] = label_config
        if estimated_tasks is not None:
            body["estimated_tasks"] = estimated_tasks
        if estimated_storage_gb is not None:
            body["estimated_storage_gb"] = estimated_storage_gb

        _response = await self._client_wrapper.httpx_client.request(
            "api/project-billing/calculate_deposit/",
            method="POST",
            json=body,
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(DepositCalculation, _response.json())
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    async def pay_deposit(
        self,
        *,
        project_id: int,
        deposit_amount: typing.Optional[float] = None,
        estimated_tasks: typing.Optional[int] = None,
        estimated_storage_gb: typing.Optional[float] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Dict[str, typing.Any]:
        """Collect security deposit for a project from organization credits."""
        body = {"project_id": project_id}
        if deposit_amount is not None:
            body["deposit_amount"] = deposit_amount
        if estimated_tasks is not None:
            body["estimated_tasks"] = estimated_tasks
        if estimated_storage_gb is not None:
            body["estimated_storage_gb"] = estimated_storage_gb

        _response = await self._client_wrapper.httpx_client.request(
            "api/project-billing/collect_deposit/",
            method="POST",
            json=body,
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return _response.json()
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    async def refund_deposit(
        self,
        *,
        project_id: int,
        reason: typing.Optional[str] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Dict[str, typing.Any]:
        """Request refund of security deposit for a completed project."""
        body = {"project_id": project_id}
        if reason is not None:
            body["reason"] = reason

        _response = await self._client_wrapper.httpx_client.request(
            "api/project-billing/refund_deposit/",
            method="POST",
            json=body,
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return _response.json()
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    async def get_project_status(
        self,
        *,
        project_id: int,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> ProjectBillingStatus:
        """Get detailed billing status for a project."""
        _response = await self._client_wrapper.httpx_client.request(
            "api/project-billing/project_status/",
            method="GET",
            params={"project_id": project_id},
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(ProjectBillingStatus, _response.json())
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    async def get_dashboard(
        self,
        *,
        organization: typing.Optional[int] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> BillingDashboard:
        """Get billing dashboard with balance, transactions, and payments."""
        params = {}
        if organization is not None:
            params["organization"] = organization

        _response = await self._client_wrapper.httpx_client.request(
            "api/billing/dashboard/",
            method="GET",
            params=params if params else None,
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return typing.cast(BillingDashboard, _response.json())
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    async def get_transactions(
        self,
        *,
        organization: typing.Optional[int] = None,
        transaction_type: typing.Optional[str] = None,
        category: typing.Optional[str] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.List[typing.Dict[str, typing.Any]]:
        """Get credit transaction history."""
        params = {}
        if organization is not None:
            params["organization"] = organization
        if transaction_type is not None:
            params["type"] = transaction_type
        if category is not None:
            params["category"] = category

        _response = await self._client_wrapper.httpx_client.request(
            "api/billing/transactions/",
            method="GET",
            params=params if params else None,
            request_options=request_options,
        )
        try:
            if 200 <= _response.status_code < 300:
                return _response.json()
            _response_json = _response.json()
        except JSONDecodeError:
            raise ApiError(status_code=_response.status_code, body=_response.text)
        raise ApiError(status_code=_response.status_code, body=_response_json)

    async def get_balance(
        self,
        *,
        organization: typing.Optional[int] = None,
        request_options: typing.Optional[RequestOptions] = None,
    ) -> typing.Dict[str, typing.Any]:
        """Get current credit balance for the organization."""
        dashboard = await self.get_dashboard(
            organization=organization,
            request_options=request_options
        )
        return dashboard.get("billing", {})

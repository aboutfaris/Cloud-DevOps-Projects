# Deploy Infrastructure and Assets to Azure using Terraform

Deploy a static "Hello World" website to Azure Storage with Terraform, store the Terraform state in a remote Azure backend, and clean up the code with variables. [Video walkthrough](https://youtube.com/live/WPvUa9-Txt8?feature=share)

## What you'll use

- Windows (64-bit) with Command Prompt and PowerShell
- Terraform (HashiCorp)
- Azure CLI and the Az PowerShell module
- An Azure subscription, and optionally Azure Cloud Shell

## Steps

### Part 1: How Terraform works

Terraform is HashiCorp's infrastructure-as-code tool for creating, changing, and destroying cloud resources. It is available as open source and as an enterprise service, and works across many providers, so you can build multi-cloud environments. The workflow is: you write infrastructure as code, run Plan, then Apply, and Terraform creates the resources on the provider (Azure, AWS, Google Cloud, Kubernetes, VMware, and others).

### Part 2: Install Terraform on Windows

1. Download the Terraform build for your operating system from the HashiCorp Terraform website (Windows, 64-bit here).
2. Extract the file and move it somewhere easy to find, for example `C:\Terraform`.
3. Open the Start menu, type `env`, and open Edit the system environment variables.
4. Select Environment Variables. Under System variables, select Path > Edit, and add your Terraform folder.
5. Open a new Command Prompt and check the install:

   ```cmd
   terraform -v
   ```

   Expected result: the output shows `Terraform v1.8.5 on windows_amd64` (your version may be newer).

### Part 3: Install the Azure tools

6. Install the [.NET 8.0 SDK](https://download.visualstudio.microsoft.com/download/pr/b6f19ef3-52ca-40b1-b78b-0712d3c8bf4d/426bd0d376479d551ce4d5ac0ecf63a5/dotnet-sdk-8.0.302-win-x64.exe).
7. Install the [Azure CLI (MSI)](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows?tabs=azure-cli#install-or-update).
8. Install the Az PowerShell module ([Microsoft's guide](https://learn.microsoft.com/en-us/powershell/azure/install-azps-windows?view=azps-12.0.0&tabs=powershell&pivots=windows-psgallery)) and sign in:

   ```powershell
   Get-ExecutionPolicy -List
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   Install-Module -Name Az -Repository PSGallery -Force
   Update-Module -Name Az -Force
   Connect-AzAccount -Tenant <tenant-id>
   ```

### Part 4: Write main.tf and deploy

9. Create `main.tf`. It creates a resource group, a StorageV2 account with static website hosting, and an `index.html` blob in the `$web` container:

   ```hcl
   provider "azurerm" {
       features {}
   }

   # Create a resource group
   resource "azurerm_resource_group" "resource_group" {
       name = "rg-terraform-demo"
       location = "eastus"
   }

   # Create a Storage Account
   # Note: Azure storage account names must be 3-24 lowercase letters and numbers, no hyphens
   resource "azurerm_storage_account" "storage_account" {
       name = "terraform-azure-houston-4"
       resource_group_name = azurerm_resource_group.resource_group.name
       location = azurerm_resource_group.resource_group.location
       account_tier ="Standard"
       account_replication_type = "LRS"
       account_kind = "StorageV2" # terraform

       static_website {
         index_document = "index.html"
       }
   }

   # Add index.html file
   resource "azurerm_storage_blob" "blob" {
       name = "index.html"
       storage_account_name = azurerm_storage_account.storage_account.name
       storage_container_name = "$web"
       type = "Block"
       content_type = "text/html"
       source_content = "<h1> Hello World, this is a website that was used to deploy terraform within azure </h1>"
   }
   ```

10. In the terminal, initialize the project:

    ```bash
    terraform init
    ```

    Expected result: `terraform init` completes and the working directory is initialized.

### Part 5: Create a remote backend for the state file

11. Create a resource group for the state:

    ```bash
    az group create --name tf-state-rg --location eastus
    ```

12. Create the storage account:

    ```bash
    az storage account create --name tftxsa1 --location eastus --resource-group tf-state-rg
    ```

    If this fails with `(SubscriptionNotFound) Subscription <subscription-id> was not found`, the CLI cannot find or access the subscription you are signed in to. Fix the sign-in or subscription selection, then run the command again.

13. Get the account key:

    ```bash
    ACCOUNT_KEY=$(az storage account keys list --resource-group tf-state-rg --account-name tftxsa1 --query '[0].value' -o tsv)
    ```

14. Create a private container for the state:

    ```bash
    az storage container create --account-name tftxsa1 --name tfstatecon --public-access off --account-key $ACCOUNT_KEY
    ```

### Part 6: Use variables

15. Create `variable.tf`:

    ```hcl
    variable "location" {
      description = "The Azure Region in which all resources in this project should be created."
    }

    variable "resource_group_name" {
      description = "The name of the resource group in which to create the storage account."
    }

    variable "storage_account_name" {
      description = "The name of the storage account to create."
    }

    variable "source_content" {
      description = "The content of the index.html file."
    }

    variable "index_document" {
      description = "The name of the index document."
    }
    ```

16. Give the variables values in `dev.tfvars`:

    ```hcl
    location = "eastus"
    resource_group_name = "tf-state-rg"
    storage_account_name = "<unique-storage-account-name>"
    index_document = "index.html"
    source_content = "<h1> Salute, this website is deployed using terraform."
    ```

17. Replace the hard-coded values in `main.tf` with the variables:

    ```hcl
    # Create a resource group
    resource "azurerm_resource_group" "tf-state-rg" {
        name = var.resource_group_name
        location = var.location
    }

    # Create a Storage Account
    resource "azurerm_storage_account" "storage_account" {
        name = var.storage_account_name
        resource_group_name = azurerm_resource_group.tf-state-rg.name
        account_tier ="Standard"
        location = var.location
        account_replication_type = "LRS"
        account_kind = "StorageV2"

        static_website {
          index_document = var.index_document
        }
    }

    # Add index.html file
    resource "azurerm_storage_blob" "tfstatecon" {
        name = var.index_document
        storage_account_name = azurerm_storage_account.storage_account.name
        storage_container_name = "$web"
        type = "Block"
        content_type = "text/html"
        source_content = var.source_content
    }
    ```

### Part 7: Plan, apply, and destroy

18. Upload the Terraform files to Azure Cloud Shell (or use your local terminal), then format and validate them:

    ```bash
    terraform fmt
    terraform validate
    ```

19. Initialize, plan, and apply:

    ```bash
    terraform init
    terraform plan -var-file="dev.tfvars"
    terraform apply -var-file="dev.tfvars"
    ```

    Expected result: in the Azure portal, the `tfstatecon` container holds a `terraform.tfstate` block blob, so the state is stored in the remote backend.

20. When you are done, remove everything:

    ```bash
    terraform destroy -var-file="dev.tfvars"
    ```

## What I learned

- Infrastructure as code makes deployments repeatable: write HCL, plan, apply, destroy.
- A remote backend in Azure Storage keeps the state file safe and shareable.
- Variables and `.tfvars` files keep `main.tf` clean and reusable.
- Getting the Azure CLI working with my IDE took about half my troubleshooting time. Running the commands in Cloud Shell, with `terraform fmt` and `terraform validate` first, was the faster path. Next, I want to fix the IDE and CLI configuration and use Terraform to automate earlier projects.

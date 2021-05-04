from collections import Counter
import requests, sys, argparse, os
from utils import (
    generate_token_OTP,
    get_beneficiaries,
    check_and_book,
    get_districts,
    get_min_age,
    beep,
    BENEFICIARIES_URL,
    WARNING_BEEP_DURATION,
)


class VaccineSlotBooking:
    """Books slot for vaccine"""

    def __init__(self, args_token):
        self.token = args_token or self.get_token()
        self.mobile = None
        self.beneficiary_details = self.get_beneficiary()

    def get_token(self):
        """Gets the token for registration"""
        self.mobile = input("Enter the registered mobile number: ")
        token = generate_token_OTP(self.mobile)
        return token

    def get_beneficiary(self):
        """Gets the beneficiary details"""
        request_header = {"Authorization": f"Bearer {self.token}"}

        # Get Beneficiaries
        print("Fetching registered beneficiaries.. ")
        beneficiary_details = get_beneficiaries(request_header)

        if len(beneficiary_details) == 0:
            print("There should be at least one beneficiary. Exiting.")
            os.system("pause")
            sys.exit(1)
        return beneficiary_details

    def vaccine_type_validation(self):
        """Validates the vaccine types"""
        # Make sure all beneficiaries have the same type of vaccine
        vaccine_types = [
            beneficiary["vaccine"] for beneficiary in self.beneficiary_details
        ]
        vaccines = Counter(vaccine_types)

        if len(vaccines.keys()) != 1:
            print(
                f"All beneficiaries in one attempt should have the same vaccine type. Found {len(vaccines.keys())}"
            )
            os.system("pause")
            sys.exit(1)

    def generate_otp(self):
        try_otp = input("Try for a new Token? (y/n): ")
        if try_otp.lower() == "y":
            if self.mobile:
                try_otp = input(
                    f"Try for OTP with mobile number {self.mobile}? (y/n) : "
                )
                if try_otp.lower() == "y":
                    token = generate_token_OTP(self.mobile)
                    token_valid = True
                else:
                    token = False
                    token_valid = False
                    print(f"Invalid response provided: {try_otp}. Exiting.")
            else:
                mobile = input(
                    f"Enter 10 digit mobile number for new OTP generation? : "
                )
                token = generate_token_OTP(mobile)
                token_valid = True
            return token, token_valid
        else:
            print("Exiting")
            os.system("pause")

    def main_slot_booking(self):
        """main function"""
        self.vaccine_type_validation()
        # Collect vaccination center preference
        district_dtls = get_districts()

        # Set filter condition
        minimum_slots = int(input("Filter out centers with availability less than: "))
        minimum_slots = (
            minimum_slots
            if minimum_slots > len(self.beneficiary_details)
            else len(self.beneficiary_details)
        )

        token_valid = True
        while token_valid:
            request_header = {"Authorization": f"Bearer {self.token}"}

            # call function to check and book slots
            token_valid = check_and_book(
                request_header, self.beneficiary_details, district_dtls, minimum_slots
            )

            # check if token is still valid
            beneficiaries_list = requests.get(BENEFICIARIES_URL, headers=request_header)
            if beneficiaries_list.status_code == 200:
                token_valid = True

            else:
                # if token invalid, regenerate OTP and new token
                beep(WARNING_BEEP_DURATION[0], WARNING_BEEP_DURATION[1])
                print("Token is INVALID.")
                token, token_valid = self.generate_otp()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="Pass token directly")
    args = parser.parse_args()
    booking_slot = VaccineSlotBooking(args.token)
    booking_slot.main_slot_booking()
